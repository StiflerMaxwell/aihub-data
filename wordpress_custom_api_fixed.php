<?php
/**
 * Plugin Name: AI工具导入API - 完整修复版
 * Description: 自定义API端点用于批量导入AI工具数据到aihub CPT，包含完整的API Key管理系统
 * Version: 2.0
 * Author: Maxwell
 */

// 防止直接访问
if (!defined('ABSPATH')) {
    exit;
}

class AIToolImportAPI {
    
    public function __construct() {
        add_action('rest_api_init', array($this, 'register_routes'));
        
        // 添加管理界面
        add_action('admin_menu', array($this, 'add_admin_menu'));
        add_action('admin_enqueue_scripts', array($this, 'enqueue_admin_scripts'));
        add_action('wp_ajax_ai_tools_generate_api_key', array($this, 'ajax_generate_api_key'));
        add_action('wp_ajax_ai_tools_delete_api_key', array($this, 'ajax_delete_api_key'));
        add_action('wp_ajax_ai_tools_toggle_api_key_status', array($this, 'ajax_toggle_api_key_status'));
        
        // 注册激活钩子
        register_activation_hook(__FILE__, array($this, 'on_activation'));
    }
    
    /**
     * 插件激活时执行
     */
    public function on_activation() {
        $this->create_api_tables();
        flush_rewrite_rules();
    }
    
    /**
     * 创建API相关数据表
     */
    public function create_api_tables() {
        global $wpdb;
        
        error_log("AI Tools: Creating API tables...");
        
        $charset_collate = $wpdb->get_charset_collate();
        
        // 创建API Key表
        $api_keys_table = $wpdb->prefix . 'ai_tools_api_keys';
        $api_keys_sql = "CREATE TABLE $api_keys_table (
            id int(11) NOT NULL AUTO_INCREMENT,
            api_key varchar(100) NOT NULL,
            name varchar(255) NOT NULL,
            description text,
            rate_limit int(11) DEFAULT 1000,
            status enum('active','inactive','suspended') DEFAULT 'active',
            created_by int(11) NOT NULL,
            created_at datetime NOT NULL,
            last_used_at datetime NULL,
            expires_at datetime NULL,
            PRIMARY KEY (id),
            UNIQUE KEY api_key (api_key),
            KEY status (status),
            KEY created_by (created_by)
        ) $charset_collate;";
        
        // 创建API使用记录表
        $api_usage_table = $wpdb->prefix . 'ai_tools_api_usage';
        $api_usage_sql = "CREATE TABLE $api_usage_table (
            id int(11) NOT NULL AUTO_INCREMENT,
            api_key varchar(100) NOT NULL,
            endpoint varchar(255) NOT NULL,
            ip_address varchar(45) NOT NULL,
            user_agent text,
            created_at datetime NOT NULL,
            PRIMARY KEY (id),
            KEY api_key (api_key),
            KEY endpoint (endpoint),
            KEY created_at (created_at)
        ) $charset_collate;";
        
        require_once(ABSPATH . 'wp-admin/includes/upgrade.php');
        
        $result1 = dbDelta($api_keys_sql);
        $result2 = dbDelta($api_usage_sql);
        
        error_log("AI Tools: Tables creation results: " . print_r(array($result1, $result2), true));
        
        // 验证表创建并创建演示key
        if ($wpdb->get_var("SHOW TABLES LIKE '$api_keys_table'") == $api_keys_table) {
            $existing_keys = $wpdb->get_var("SELECT COUNT(*) FROM $api_keys_table");
            if ($existing_keys == 0) {
                $demo_key = 'ak_demo_' . bin2hex(random_bytes(20));
                $wpdb->insert($api_keys_table, array(
                    'api_key' => $demo_key,
                    'name' => '演示API Key',
                    'description' => '系统自动创建的演示API Key',
                    'rate_limit' => 100,
                    'status' => 'active',
                    'created_by' => 1,
                    'created_at' => current_time('mysql')
                ));
                update_option('ai_tools_demo_api_key', $demo_key);
                error_log("AI Tools: Demo key created: $demo_key");
            }
        }
        
        return true;
    }
    
    /**
     * 注册API路由
     */
    public function register_routes() {
        // 工具相关端点
        register_rest_route('ai-tools/v1', '/tools', array(
            'methods' => 'GET',
            'callback' => array($this, 'get_all_tools'),
            'permission_callback' => array($this, 'check_api_key'),
            'args' => array(
                'page' => array('default' => 1, 'sanitize_callback' => 'absint'),
                'per_page' => array('default' => 20, 'sanitize_callback' => 'absint'),
                'search' => array('sanitize_callback' => 'sanitize_text_field'),
                'category' => array('sanitize_callback' => 'sanitize_text_field'),
                'pricing' => array('sanitize_callback' => 'sanitize_text_field'),
                'input_type' => array('sanitize_callback' => 'sanitize_text_field'),
                'output_type' => array('sanitize_callback' => 'sanitize_text_field')
            )
        ));

        register_rest_route('ai-tools/v1', '/tools/(?P<id>\d+)', array(
            'methods' => 'GET',
            'callback' => array($this, 'get_single_tool'),
            'permission_callback' => array($this, 'check_api_key'),
            'args' => array(
                'id' => array('validate_callback' => function($param) {
                    return is_numeric($param);
                })
            )
        ));

        register_rest_route('ai-tools/v1', '/tools/by-url', array(
            'methods' => 'GET',
            'callback' => array($this, 'get_tool_by_url'),
            'permission_callback' => array($this, 'check_api_key'),
            'args' => array(
                'url' => array('required' => true, 'sanitize_callback' => 'esc_url_raw')
            )
        ));

        register_rest_route('ai-tools/v1', '/tools/random', array(
            'methods' => 'GET',
            'callback' => array($this, 'get_random_tools'),
            'permission_callback' => array($this, 'check_api_key'),
            'args' => array(
                'count' => array('default' => 5, 'sanitize_callback' => 'absint'),
                'category' => array('sanitize_callback' => 'sanitize_text_field')
            )
        ));

        register_rest_route('ai-tools/v1', '/tools/popular', array(
            'methods' => 'GET',
            'callback' => array($this, 'get_popular_tools'),
            'permission_callback' => array($this, 'check_api_key'),
            'args' => array(
                'count' => array('default' => 10, 'sanitize_callback' => 'absint')
            )
        ));

        // 分类和标签端点
        register_rest_route('ai-tools/v1', '/categories', array(
            'methods' => 'GET',
            'callback' => array($this, 'get_categories'),
            'permission_callback' => array($this, 'check_api_key')
        ));

        register_rest_route('ai-tools/v1', '/tags', array(
            'methods' => 'GET',
            'callback' => array($this, 'get_tags'),
            'permission_callback' => array($this, 'check_api_key')
        ));

        // 统计端点
        register_rest_route('ai-tools/v1', '/stats', array(
            'methods' => 'GET',
            'callback' => array($this, 'get_statistics'),
            'permission_callback' => array($this, 'check_api_key')
        ));

        // API Key管理端点（仅管理员）
        register_rest_route('ai-tools/v1', '/generate-api-key', array(
            'methods' => 'POST',
            'callback' => array($this, 'generate_api_key'),
            'permission_callback' => array($this, 'check_admin_permissions'),
            'args' => array(
                'name' => array('required' => true, 'sanitize_callback' => 'sanitize_text_field'),
                'description' => array('sanitize_callback' => 'sanitize_textarea_field'),
                'rate_limit' => array('default' => 1000, 'sanitize_callback' => 'absint')
            )
        ));

        register_rest_route('ai-tools/v1', '/api-keys', array(
            'methods' => 'GET',
            'callback' => array($this, 'list_api_keys'),
            'permission_callback' => array($this, 'check_admin_permissions')
        ));

        register_rest_route('ai-tools/v1', '/api-keys/(?P<id>\d+)', array(
            'methods' => 'DELETE',
            'callback' => array($this, 'delete_api_key'),
            'permission_callback' => array($this, 'check_admin_permissions'),
            'args' => array(
                'id' => array('validate_callback' => function($param) {
                    return is_numeric($param);
                })
            )
        ));

        // 测试端点
        register_rest_route('ai-tools/v1', '/test', array(
            'methods' => 'GET',
            'callback' => array($this, 'test_connection'),
            'permission_callback' => array($this, 'check_api_key')
        ));
    }
    
    /**
     * 生成API Key
     */
    public function generate_api_key($request) {
        error_log("AI Tools API: generate_api_key called");
        
        $name = sanitize_text_field($request->get_param('name'));
        $description = sanitize_textarea_field($request->get_param('description') ?: '');
        $rate_limit = intval($request->get_param('rate_limit')) ?: 1000;
        
        if (empty($name)) {
            return new WP_REST_Response(array(
                'success' => false,
                'message' => '名称不能为空'
            ), 400);
        }
        
        // 生成API Key
        $api_key = 'ak_' . bin2hex(random_bytes(24));
        
        global $wpdb;
        $table_name = $wpdb->prefix . 'ai_tools_api_keys';
        
        // 确保表存在
        if (!$wpdb->get_var("SHOW TABLES LIKE '$table_name'")) {
            $this->create_api_tables();
        }
        
        $current_user_id = get_current_user_id() ?: 1;
        
        $result = $wpdb->insert($table_name, array(
            'api_key' => $api_key,
            'name' => $name,
            'description' => $description,
            'rate_limit' => $rate_limit,
            'status' => 'active',
            'created_by' => $current_user_id,
            'created_at' => current_time('mysql')
        ), array('%s', '%s', '%s', '%d', '%s', '%d', '%s'));
        
        if ($result === false) {
            error_log("AI Tools API: Insert failed: " . $wpdb->last_error);
            return new WP_REST_Response(array(
                'success' => false,
                'message' => '创建API Key失败: ' . $wpdb->last_error
            ), 500);
        }
        
        return new WP_REST_Response(array(
            'success' => true,
            'message' => 'API Key创建成功',
            'data' => array(
                'id' => $wpdb->insert_id,
                'api_key' => $api_key,
                'name' => $name,
                'rate_limit' => $rate_limit,
                'created_at' => current_time('mysql')
            )
        ), 201);
    }
    
    /**
     * 获取API Key列表
     */
    public function list_api_keys($request) {
        global $wpdb;
        $table_name = $wpdb->prefix . 'ai_tools_api_keys';
        
        $keys = $wpdb->get_results("
            SELECT id, name, description, rate_limit, status, created_at, last_used_at,
                   CONCAT(SUBSTRING(api_key, 1, 12), '...') as api_key_preview,
                   api_key as full_key
            FROM $table_name 
            ORDER BY created_at DESC
        ");
        
        return new WP_REST_Response(array(
            'success' => true,
            'data' => $keys
        ), 200);
    }
    
    /**
     * 删除API Key
     */
    public function delete_api_key($request) {
        $key_id = intval($request->get_param('id'));
        
        global $wpdb;
        $table_name = $wpdb->prefix . 'ai_tools_api_keys';
        
        $result = $wpdb->delete($table_name, array('id' => $key_id), array('%d'));
        
        if ($result === false) {
            return new WP_REST_Response(array(
                'success' => false,
                'message' => '删除失败'
            ), 500);
        }
        
        return new WP_REST_Response(array(
            'success' => true,
            'message' => 'API Key已删除'
        ), 200);
    }
    
    /**
     * 获取AI工具列表（增强版）
     */
    public function get_all_tools($request) {
        $page = $request->get_param('page') ?: 1;
        $per_page = $request->get_param('per_page') ?: 20;
        $search = $request->get_param('search');
        $category = $request->get_param('category');
        $pricing = $request->get_param('pricing');
        $input_type = $request->get_param('input_type');
        $output_type = $request->get_param('output_type');
        
        // 确保 per_page 在合理范围内
        $per_page = min(max(1, intval($per_page)), 100);
        
        // 构建查询参数
        $args = array(
            'post_type' => 'aihub',
            'post_status' => 'publish',
            'posts_per_page' => $per_page,
            'paged' => $page,
            'meta_query' => array()
        );
        
        // 搜索
        if (!empty($search)) {
            $args['s'] = sanitize_text_field($search);
        }
        
        // 按人气排序
        $args['meta_key'] = 'popularity_score';
        $args['orderby'] = 'meta_value_num';
        $args['order'] = 'DESC';
        
        // 分类筛选
        if (!empty($category)) {
            $args['tax_query'] = array(
                array(
                    'taxonomy' => 'category',
                    'field' => 'slug',
                    'terms' => sanitize_title($category)
                )
            );
        }
        
        // 定价筛选
        if (!empty($pricing)) {
            $args['meta_query'][] = array(
                'key' => 'general_price_tag',
                'value' => sanitize_text_field($pricing),
                'compare' => 'LIKE'
            );
        }
        
        // 输入类型筛选
        if (!empty($input_type)) {
            $args['meta_query'][] = array(
                'key' => 'inputs',
                'value' => sanitize_text_field($input_type),
                'compare' => 'LIKE'
            );
        }
        
        // 输出类型筛选
        if (!empty($output_type)) {
            $args['meta_query'][] = array(
                'key' => 'outputs',
                'value' => sanitize_text_field($output_type),
                'compare' => 'LIKE'
            );
        }
        
        $query = new WP_Query($args);
        $tools = array();
        
        if ($query->have_posts()) {
            while ($query->have_posts()) {
                $query->the_post();
                $post_id = get_the_ID();
                $fields = get_fields($post_id);
                
                // 获取分类和标签
                $categories = wp_get_post_terms($post_id, 'category', array('fields' => 'names'));
                $tags = wp_get_post_terms($post_id, 'post_tag', array('fields' => 'names'));
                
                // 处理logo图片URL
                $logo_img = $fields['logo_img'] ?? null;
                $logo_img_url = '';
                if ($logo_img) {
                    if (is_array($logo_img)) {
                        $logo_img_url = $logo_img['url'] ?? '';
                    } elseif (is_numeric($logo_img)) {
                        $logo_img_url = wp_get_attachment_url($logo_img);
                    } else {
                        $logo_img_url = $logo_img;
                    }
                }
                
                // 处理概览图片URL
                $overview_img = $fields['overview_img'] ?? null;
                $overview_img_url = '';
                if ($overview_img) {
                    if (is_array($overview_img)) {
                        $overview_img_url = $overview_img['url'] ?? '';
                    } elseif (is_numeric($overview_img)) {
                        $overview_img_url = wp_get_attachment_url($overview_img);
                    } else {
                        $overview_img_url = $overview_img;
                    }
                }
                
                // 处理定价详情
                $pricing_details = $fields['pricing_details'] ?? array();
                if (is_string($pricing_details)) {
                    $pricing_details = json_decode($pricing_details, true) ?: array();
                }
                
                // 处理输入输出类型
                $inputs = $fields['inputs'] ?? array();
                $outputs = $fields['outputs'] ?? array();
                if (is_string($inputs)) {
                    $inputs = array_filter(array_map('trim', explode(',', $inputs)));
                }
                if (is_string($outputs)) {
                    $outputs = array_filter(array_map('trim', explode(',', $outputs)));
                }
                
                // 处理功能列表
                $features = array();
                if (!empty($fields['features']) && is_array($fields['features'])) {
                    foreach ($fields['features'] as $feature) {
                        if (is_array($feature) && !empty($feature['feature_item'])) {
                            $features[] = $feature['feature_item'];
                        } elseif (is_string($feature) && !empty($feature)) {
                            $features[] = $feature;
                        }
                    }
                }
                
                $tools[] = array(
                    'id' => $post_id,
                    'title' => get_the_title(),
                    'slug' => get_post_field('post_name', $post_id),
                    'url' => get_permalink(),
                    'excerpt' => get_the_excerpt(),
                    'date_created' => get_the_date('c'),
                    'date_modified' => get_the_modified_date('c'),
                    
                    // 产品信息
                    'product_name' => $fields['product_name'] ?? get_the_title(),
                    'product_url' => $fields['product_url'] ?? '',
                    'short_introduction' => $fields['short_introduction'] ?? get_the_excerpt(),
                    'author_company' => $fields['author_company'] ?? '',
                    'primary_task' => $fields['primary_task'] ?? '',
                    
                    // 定价信息
                    'general_price_tag' => $fields['general_price_tag'] ?? 'Unknown',
                    'pricing_details' => array(
                        'pricing_model' => $pricing_details['pricing_model'] ?? $fields['general_price_tag'] ?? 'Unknown',
                        'currency' => $pricing_details['currency'] ?? 'USD',
                        'paid_options_from' => floatval($pricing_details['paid_options_from'] ?? 0)
                    ),
                    
                    // 媒体资源
                    'logo_img_url' => $logo_img_url,
                    'overview_img_url' => $overview_img_url,
                    
                    // 评分和流行度
                    'average_rating' => floatval($fields['average_rating'] ?? 0),
                    'popularity_score' => floatval($fields['popularity_score'] ?? 0),
                    'user_ratings_count' => intval($fields['user_ratings_count'] ?? 0),
                    'is_verified_tool' => boolval($fields['is_verified_tool'] ?? false),
                    
                    // 功能和类型
                    'inputs' => is_array($inputs) ? $inputs : array(),
                    'outputs' => is_array($outputs) ? $outputs : array(),
                    'features' => $features,
                    
                    // 分类和标签
                    'category' => $fields['category'] ?? (isset($categories[0]) ? $categories[0] : ''),
                    'categories' => is_array($categories) ? $categories : array(),
                    'tags' => is_array($tags) ? $tags : array(),
                    
                    // 发布信息
                    'initial_release_date' => $fields['initial_release_date'] ?? ''
                );
            }
        }
        wp_reset_postdata();
        
        $response = new WP_REST_Response(array(
            'success' => true,
            'data' => $tools,
            'pagination' => array(
                'page' => intval($page),
                'per_page' => intval($per_page),
                'total' => $query->found_posts,
                'total_pages' => $query->max_num_pages
            ),
            'timestamp' => current_time('c')
        ), 200);
        
        $response->header('Access-Control-Allow-Origin', '*');
        return $response;
    }
    
    /**
     * 测试连接
     */
    public function test_connection($request) {
        return new WP_REST_Response(array(
            'success' => true,
            'message' => 'API连接成功',
            'timestamp' => current_time('c')
        ), 200);
    }
    
    /**
     * 检查管理员权限
     */
    public function check_admin_permissions() {
        return current_user_can('manage_options');
    }
    
    /**
     * 检查API Key权限
     */
    public function check_api_key($request) {
        $api_key = $this->get_api_key_from_request($request);
        
        if (empty($api_key)) {
            return new WP_Error('missing_api_key', 'API Key是必需的', array('status' => 401));
        }
        
        global $wpdb;
        $table_name = $wpdb->prefix . 'ai_tools_api_keys';
        
        $key_data = $wpdb->get_row($wpdb->prepare("
            SELECT * FROM $table_name 
            WHERE api_key = %s AND status = 'active'
        ", $api_key));
        
        if (!$key_data) {
            return new WP_Error('invalid_api_key', 'API Key无效', array('status' => 401));
        }
        
        // 记录使用
        $wpdb->update($table_name, 
            array('last_used_at' => current_time('mysql')), 
            array('api_key' => $api_key),
            array('%s'), array('%s')
        );
        
        return true;
    }
    
    /**
     * 从请求中获取API Key
     */
    private function get_api_key_from_request($request) {
        // 从头部获取
        $api_key = $request->get_header('X-API-Key');
        if (!empty($api_key)) return $api_key;
        
        // 从Authorization头获取
        $auth_header = $request->get_header('Authorization');
        if (!empty($auth_header) && strpos($auth_header, 'Bearer ') === 0) {
            return substr($auth_header, 7);
        }
        
        // 从参数获取
        return $request->get_param('api_key');
    }
    
    // ========== WordPress管理界面 ==========
    
    /**
     * 添加管理菜单
     */
    public function add_admin_menu() {
        add_management_page(
            'AI工具API管理',
            'AI工具API',
            'manage_options',
            'ai-tools-api-keys',
            array($this, 'admin_page')
        );
    }
    
    /**
     * 加载管理页面脚本
     */
    public function enqueue_admin_scripts($hook) {
        if ($hook !== 'tools_page_ai-tools-api-keys') {
            return;
        }
        
        wp_enqueue_script('jquery');
        
        $inline_js = '
        jQuery(document).ready(function($) {
            $("#generate-api-key-form").on("submit", function(e) {
                e.preventDefault();
                
                var $form = $(this);
                var $button = $form.find("input[type=submit]");
                var $spinner = $form.find(".spinner");
                
                $button.prop("disabled", true);
                $spinner.addClass("is-active");
                
                $.post(ajaxurl, {
                    action: "ai_tools_generate_api_key",
                    nonce: aiToolsAjax.nonce,
                    name: $("#api_key_name").val(),
                    description: $("#api_key_description").val(),
                    rate_limit: $("#api_key_rate_limit").val()
                }, function(response) {
                    if (response.success) {
                        alert("API Key生成成功！");
                        location.reload();
                    } else {
                        alert("生成失败：" + (response.data || "未知错误"));
                    }
                }).fail(function() {
                    alert("请求失败，请重试");
                }).always(function() {
                    $button.prop("disabled", false);
                    $spinner.removeClass("is-active");
                });
            });
            
            $(".show-full-key").on("click", function() {
                var fullKey = $(this).data("full-key");
                $("#full-api-key").val(fullKey);
                $("#api-key-modal").show();
            });
            
            $(".close, .ai-tools-modal").on("click", function(e) {
                if (e.target === this) {
                    $("#api-key-modal").hide();
                }
            });
            
            $(".copy-api-key").on("click", function() {
                var $input = $("#full-api-key");
                $input.select();
                document.execCommand("copy");
                $(this).text("已复制！");
                setTimeout(() => {
                    $(this).text("复制");
                }, 2000);
            });
            
            $(".delete-key").on("click", function() {
                var keyId = $(this).data("key-id");
                var keyName = $(this).data("key-name");
                
                if (confirm("确定要删除API Key \"" + keyName + "\" 吗？")) {
                    $.post(ajaxurl, {
                        action: "ai_tools_delete_api_key",
                        nonce: aiToolsAjax.nonce,
                        key_id: keyId
                    }, function(response) {
                        if (response.success) {
                            alert("删除成功！");
                            location.reload();
                        } else {
                            alert("删除失败：" + (response.data || "未知错误"));
                        }
                    });
                }
            });
        });
        ';
        
        wp_add_inline_script('jquery', $inline_js);
        
        wp_localize_script('jquery', 'aiToolsAjax', array(
            'ajaxurl' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('ai_tools_api_nonce')
        ));
    }
    
    /**
     * 管理页面HTML
     */
    public function admin_page() {
        global $wpdb;
        
        $table_name = $wpdb->prefix . 'ai_tools_api_keys';
        $api_keys = $wpdb->get_results("SELECT * FROM $table_name ORDER BY created_at DESC");
        
        ?>
        <div class="wrap">
            <h1>🤖 AI工具API Key管理</h1>
            
            <!-- 概览统计 -->
            <div class="ai-tools-stats">
                <div class="stats-card">
                    <h3>总API Key数</h3>
                    <span class="stats-number"><?php echo count($api_keys); ?></span>
                </div>
                <div class="stats-card">
                    <h3>活跃Key数</h3>
                    <span class="stats-number"><?php echo count(array_filter($api_keys, function($key) { return $key->status === 'active'; })); ?></span>
                </div>
            </div>
            
            <!-- 生成新API Key表单 -->
            <div class="ai-tools-generate-form">
                <h2>✨ 生成新的API Key</h2>
                <form id="generate-api-key-form">
                    <table class="form-table">
                        <tr>
                            <th><label for="api_key_name">名称</label></th>
                            <td><input type="text" id="api_key_name" name="name" class="regular-text" required /></td>
                        </tr>
                        <tr>
                            <th><label for="api_key_description">描述</label></th>
                            <td><textarea id="api_key_description" name="description" class="regular-text" rows="3"></textarea></td>
                        </tr>
                        <tr>
                            <th><label for="api_key_rate_limit">速率限制（每小时）</label></th>
                            <td><input type="number" id="api_key_rate_limit" name="rate_limit" value="1000" min="1" max="10000" /></td>
                        </tr>
                    </table>
                    <p class="submit">
                        <input type="submit" class="button button-primary" value="生成API Key" />
                        <span class="spinner"></span>
                    </p>
                </form>
            </div>
            
            <!-- API Key列表 -->
            <div class="ai-tools-api-keys-list">
                <h2>🔑 现有API Key</h2>
                
                <?php if (empty($api_keys)): ?>
                    <p>还没有API Key。请先生成一个。</p>
                <?php else: ?>
                    <table class="wp-list-table widefat fixed striped">
                        <thead>
                            <tr>
                                <th>名称</th>
                                <th>API Key</th>
                                <th>状态</th>
                                <th>速率限制</th>
                                <th>创建时间</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php foreach ($api_keys as $key): ?>
                                <tr>
                                    <td>
                                        <strong><?php echo esc_html($key->name); ?></strong>
                                        <?php if ($key->description): ?>
                                            <br><small><?php echo esc_html($key->description); ?></small>
                                        <?php endif; ?>
                                    </td>
                                    <td>
                                        <code><?php echo substr($key->api_key, 0, 12) . '...'; ?></code>
                                        <button type="button" class="button button-small show-full-key" data-full-key="<?php echo esc_attr($key->api_key); ?>">显示完整</button>
                                    </td>
                                    <td>
                                        <span class="status-badge status-<?php echo $key->status; ?>">
                                            <?php echo ucfirst($key->status); ?>
                                        </span>
                                    </td>
                                    <td><?php echo number_format($key->rate_limit); ?>/小时</td>
                                    <td><?php echo date('Y-m-d H:i', strtotime($key->created_at)); ?></td>
                                    <td>
                                        <button type="button" class="button button-small delete-key" data-key-id="<?php echo $key->id; ?>" data-key-name="<?php echo esc_attr($key->name); ?>">删除</button>
                                    </td>
                                </tr>
                            <?php endforeach; ?>
                        </tbody>
                    </table>
                <?php endif; ?>
            </div>
        </div>
        
        <!-- 模态框 -->
        <div id="api-key-modal" class="ai-tools-modal" style="display: none;">
            <div class="modal-content">
                <span class="close">&times;</span>
                <h3>完整API Key</h3>
                <p>请复制并安全保存此API Key：</p>
                <div class="api-key-full">
                    <input type="text" id="full-api-key" readonly />
                    <button type="button" class="button copy-api-key">复制</button>
                </div>
                <p class="warning">⚠️ 请妥善保管此API Key，不要在公共场所暴露。</p>
            </div>
        </div>
        
        <style>
        .ai-tools-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
        .stats-card { background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; border: 1px solid #dee2e6; }
        .stats-number { font-size: 32px; font-weight: bold; color: #007cba; display: block; }
        .ai-tools-generate-form, .ai-tools-api-keys-list { background: #fff; padding: 20px; margin: 20px 0; border: 1px solid #ccd0d4; border-radius: 4px; }
        .status-badge { padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
        .status-active { background: #00a32a; color: white; }
        .status-inactive { background: #ddd; color: #666; }
        .ai-tools-modal { position: fixed; z-index: 9999; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.5); }
        .modal-content { background-color: #fefefe; margin: 15% auto; padding: 20px; border-radius: 8px; width: 500px; max-width: 90%; position: relative; }
        .close { color: #aaa; float: right; font-size: 28px; font-weight: bold; cursor: pointer; position: absolute; right: 15px; top: 10px; }
        .close:hover { color: #000; }
        .api-key-full { display: flex; gap: 10px; margin: 15px 0; }
        .api-key-full input { flex: 1; padding: 8px; font-family: monospace; }
        .warning { background: #fff3cd; border: 1px solid #ffeaa7; color: #856404; padding: 10px; border-radius: 4px; }
        .spinner.is-active { visibility: visible; }
        </style>
        <?php
    }
    
    /**
     * AJAX: 生成API Key
     */
    public function ajax_generate_api_key() {
        // 检查nonce
        if (!wp_verify_nonce($_POST['nonce'] ?? '', 'ai_tools_api_nonce')) {
            wp_send_json_error('安全验证失败');
            return;
        }
        
        if (!current_user_can('manage_options')) {
            wp_send_json_error('权限不足');
            return;
        }
        
        $name = sanitize_text_field($_POST['name'] ?? '');
        $description = sanitize_textarea_field($_POST['description'] ?? '');
        $rate_limit = intval($_POST['rate_limit'] ?? 1000);
        
        if (empty($name)) {
            wp_send_json_error('名称不能为空');
            return;
        }
        
        // 生成API Key
        $api_key = 'ak_' . bin2hex(random_bytes(24));
        
        global $wpdb;
        $table_name = $wpdb->prefix . 'ai_tools_api_keys';
        
        // 确保表存在
        if (!$wpdb->get_var("SHOW TABLES LIKE '$table_name'")) {
            $this->create_api_tables();
        }
        
        $result = $wpdb->insert($table_name, array(
            'api_key' => $api_key,
            'name' => $name,
            'description' => $description,
            'rate_limit' => $rate_limit,
            'status' => 'active',
            'created_by' => get_current_user_id() ?: 1,
            'created_at' => current_time('mysql')
        ), array('%s', '%s', '%s', '%d', '%s', '%d', '%s'));
        
        if ($result === false) {
            wp_send_json_error('创建失败: ' . $wpdb->last_error);
            return;
        }
        
        wp_send_json_success(array(
            'api_key' => $api_key,
            'name' => $name,
            'message' => 'API Key创建成功'
        ));
    }
    
    /**
     * AJAX: 删除API Key
     */
    public function ajax_delete_api_key() {
        if (!wp_verify_nonce($_POST['nonce'] ?? '', 'ai_tools_api_nonce')) {
            wp_send_json_error('安全验证失败');
            return;
        }
        
        if (!current_user_can('manage_options')) {
            wp_send_json_error('权限不足');
            return;
        }
        
        $key_id = intval($_POST['key_id'] ?? 0);
        
        global $wpdb;
        $table_name = $wpdb->prefix . 'ai_tools_api_keys';
        
        $result = $wpdb->delete($table_name, array('id' => $key_id), array('%d'));
        
        if ($result === false) {
            wp_send_json_error('删除失败');
            return;
        }
        
        wp_send_json_success('API Key已删除');
    }

    /**
     * 获取单个工具详情
     */
    public function get_single_tool($request) {
        $tool_id = intval($request->get_param('id'));
        
        $post = get_post($tool_id);
        if (!$post || $post->post_type !== 'aihub' || $post->post_status !== 'publish') {
            return new WP_REST_Response(array(
                'success' => false,
                'message' => '工具不存在',
                'code' => 'not_found'
            ), 404);
        }
        
        $fields = get_fields($tool_id);
        $categories = wp_get_post_terms($tool_id, 'category', array('fields' => 'names'));
        $tags = wp_get_post_terms($tool_id, 'post_tag', array('fields' => 'names'));
        
        // 处理ACF字段
        $pros_list = array();
        if (!empty($fields['pros_list']) && is_array($fields['pros_list'])) {
            foreach ($fields['pros_list'] as $pro) {
                if (is_array($pro) && !empty($pro['pro_item'])) {
                    $pros_list[] = array('pro_item' => $pro['pro_item']);
                }
            }
        }
        
        $cons_list = array();
        if (!empty($fields['cons_list']) && is_array($fields['cons_list'])) {
            foreach ($fields['cons_list'] as $con) {
                if (is_array($con) && !empty($con['con_item'])) {
                    $cons_list[] = array('con_item' => $con['con_item']);
                }
            }
        }
        
        $related_tasks = array();
        if (!empty($fields['related_tasks']) && is_array($fields['related_tasks'])) {
            foreach ($fields['related_tasks'] as $task) {
                if (is_array($task) && !empty($task['task_item'])) {
                    $related_tasks[] = array('task_item' => $task['task_item']);
                }
            }
        }
        
        $alternatives = array();
        if (!empty($fields['alternatives']) && is_array($fields['alternatives'])) {
            foreach ($fields['alternatives'] as $alt) {
                if (is_array($alt)) {
                    $alternatives[] = array(
                        'alternative_tool_name' => $alt['alternative_tool_name'] ?? '',
                        'alternative_tool_url' => $alt['alternative_tool_url'] ?? '',
                        'relationship_type' => $alt['relationship_type'] ?? 'Alternative'
                    );
                }
            }
        }
        
        $releases = array();
        if (!empty($fields['releases']) && is_array($fields['releases'])) {
            foreach ($fields['releases'] as $release) {
                if (is_array($release)) {
                    $releases[] = array(
                        'release_product_name' => $release['release_product_name'] ?? '',
                        'release_date' => $release['release_date'] ?? '',
                        'release_notes' => $release['release_notes'] ?? '',
                        'release_author' => $release['release_author'] ?? ''
                    );
                }
            }
        }
        
        $tool_data = array(
            'id' => $tool_id,
            'title' => $post->post_title,
            'content' => $post->post_content,
            'url' => get_permalink($tool_id),
            'product_story' => $fields['product_story'] ?? '',
            'author_company' => $fields['author_company'] ?? '',
            'initial_release_date' => $fields['initial_release_date'] ?? '',
            'user_ratings_count' => intval($fields['user_ratings_count'] ?? 0),
            'average_rating' => floatval($fields['average_rating'] ?? 0),
            'pros_list' => $pros_list,
            'cons_list' => $cons_list,
            'related_tasks' => $related_tasks,
            'alternatives' => $alternatives,
            'releases' => $releases
        );
        
        return new WP_REST_Response(array(
            'success' => true,
            'data' => $tool_data,
            'timestamp' => current_time('c')
        ), 200);
    }

    /**
     * 通过URL查找工具
     */
    public function get_tool_by_url($request) {
        $url = esc_url_raw($request->get_param('url'));
        
        $args = array(
            'post_type' => 'aihub',
            'post_status' => 'publish',
            'meta_query' => array(
                array(
                    'key' => 'product_url',
                    'value' => $url,
                    'compare' => '='
                )
            ),
            'posts_per_page' => 1
        );
        
        $query = new WP_Query($args);
        
        if (!$query->have_posts()) {
            return new WP_REST_Response(array(
                'success' => false,
                'message' => '未找到对应的工具',
                'code' => 'not_found'
            ), 404);
        }
        
        $post = $query->posts[0];
        
        return $this->get_single_tool(new WP_REST_Request('GET', '/tools/' . $post->ID));
    }

    /**
     * 获取随机工具
     */
    public function get_random_tools($request) {
        $count = min(max(1, intval($request->get_param('count'))), 20);
        $category = $request->get_param('category');
        
        $args = array(
            'post_type' => 'aihub',
            'post_status' => 'publish',
            'posts_per_page' => $count,
            'orderby' => 'rand'
        );
        
        if (!empty($category)) {
            $args['tax_query'] = array(
                array(
                    'taxonomy' => 'category',
                    'field' => 'slug',
                    'terms' => sanitize_title($category)
                )
            );
        }
        
        $query = new WP_Query($args);
        $tools = array();
        
        if ($query->have_posts()) {
            while ($query->have_posts()) {
                $query->the_post();
                $post_id = get_the_ID();
                $fields = get_fields($post_id);
                
                $tools[] = array(
                    'id' => $post_id,
                    'title' => get_the_title(),
                    'url' => get_permalink(),
                    'product_url' => $fields['product_url'] ?? '',
                    'short_introduction' => $fields['short_introduction'] ?? get_the_excerpt(),
                    'general_price_tag' => $fields['general_price_tag'] ?? 'Unknown',
                    'average_rating' => floatval($fields['average_rating'] ?? 0),
                    'popularity_score' => floatval($fields['popularity_score'] ?? 0)
                );
            }
        }
        wp_reset_postdata();
        
        return new WP_REST_Response(array(
            'success' => true,
            'data' => $tools,
            'count' => count($tools),
            'timestamp' => current_time('c')
        ), 200);
    }

    /**
     * 获取热门工具
     */
    public function get_popular_tools($request) {
        $count = min(max(1, intval($request->get_param('count'))), 50);
        
        $args = array(
            'post_type' => 'aihub',
            'post_status' => 'publish',
            'posts_per_page' => $count,
            'meta_key' => 'popularity_score',
            'orderby' => 'meta_value_num',
            'order' => 'DESC'
        );
        
        $query = new WP_Query($args);
        $tools = array();
        
        if ($query->have_posts()) {
            while ($query->have_posts()) {
                $query->the_post();
                $post_id = get_the_ID();
                $fields = get_fields($post_id);
                
                $tools[] = array(
                    'id' => $post_id,
                    'title' => get_the_title(),
                    'url' => get_permalink(),
                    'product_url' => $fields['product_url'] ?? '',
                    'short_introduction' => $fields['short_introduction'] ?? get_the_excerpt(),
                    'general_price_tag' => $fields['general_price_tag'] ?? 'Unknown',
                    'average_rating' => floatval($fields['average_rating'] ?? 0),
                    'popularity_score' => floatval($fields['popularity_score'] ?? 0),
                    'is_verified_tool' => boolval($fields['is_verified_tool'] ?? false)
                );
            }
        }
        wp_reset_postdata();
        
        return new WP_REST_Response(array(
            'success' => true,
            'data' => $tools,
            'count' => count($tools),
            'timestamp' => current_time('c')
        ), 200);
    }

    /**
     * 获取分类列表
     */
    public function get_categories($request) {
        $categories = get_terms(array(
            'taxonomy' => 'category',
            'hide_empty' => true
        ));
        
        $formatted_categories = array();
        foreach ($categories as $category) {
            $formatted_categories[] = array(
                'id' => $category->term_id,
                'name' => $category->name,
                'slug' => $category->slug,
                'count' => $category->count,
                'description' => $category->description
            );
        }
        
        return new WP_REST_Response(array(
            'success' => true,
            'data' => $formatted_categories,
            'count' => count($formatted_categories),
            'timestamp' => current_time('c')
        ), 200);
    }

    /**
     * 获取标签列表
     */
    public function get_tags($request) {
        $tags = get_terms(array(
            'taxonomy' => 'post_tag',
            'hide_empty' => true,
            'number' => 50
        ));
        
        $formatted_tags = array();
        foreach ($tags as $tag) {
            $formatted_tags[] = array(
                'id' => $tag->term_id,
                'name' => $tag->name,
                'slug' => $tag->slug,
                'count' => $tag->count
            );
        }
        
        return new WP_REST_Response(array(
            'success' => true,
            'data' => $formatted_tags,
            'count' => count($formatted_tags),
            'timestamp' => current_time('c')
        ), 200);
    }

    /**
     * 获取统计信息
     */
    public function get_statistics($request) {
        global $wpdb;
        
        // 总工具数
        $total_tools = wp_count_posts('aihub')->publish;
        
        // 分类统计
        $categories = get_terms(array(
            'taxonomy' => 'category',
            'hide_empty' => true,
            'number' => 10
        ));
        
        $category_stats = array();
        foreach ($categories as $category) {
            $category_stats[] = array(
                'name' => $category->name,
                'count' => $category->count
            );
        }
        
        // 定价统计
        $pricing_stats = $wpdb->get_results("
            SELECT meta_value as pricing, COUNT(*) as count 
            FROM {$wpdb->postmeta} pm
            JOIN {$wpdb->posts} p ON pm.post_id = p.ID
            WHERE pm.meta_key = 'general_price_tag' 
            AND p.post_type = 'aihub' 
            AND p.post_status = 'publish'
            AND pm.meta_value != ''
            GROUP BY pm.meta_value
            ORDER BY count DESC
        ");
        
        $formatted_pricing = array();
        foreach ($pricing_stats as $stat) {
            $formatted_pricing[] = array(
                'pricing' => $stat->pricing,
                'count' => (int)$stat->count
            );
        }
        
        // 最后更新时间
        $last_updated = $wpdb->get_var("
            SELECT post_modified 
            FROM {$wpdb->posts} 
            WHERE post_type = 'aihub' 
            AND post_status = 'publish' 
            ORDER BY post_modified DESC 
            LIMIT 1
        ");
        
        return new WP_REST_Response(array(
            'success' => true,
            'data' => array(
                'total_tools' => (int)$total_tools,
                'categories' => $category_stats,
                'pricing' => $formatted_pricing,
                'last_updated' => $last_updated
            )
        ), 200);
    }
}

// 初始化插件
new AIToolImportAPI();

/**
 * 激活插件时的处理
 */
register_activation_hook(__FILE__, function() {
    $plugin = new AIToolImportAPI();
    $plugin->create_api_tables();
    flush_rewrite_rules();
});

/**
 * 停用插件时的处理
 */
register_deactivation_hook(__FILE__, function() {
    flush_rewrite_rules();
});

?> 