<?php
/**
 * Plugin Name: AI工具导入API - MVP版本
 * Description: 支持MVP版本6个JSON字段的自定义API端点，输出扁平化结构
 * Version: 3.0 - MVP
 * Author: Maxwell
 */

// 防止直接访问
if (!defined('ABSPATH')) {
    exit;
}

class AIToolImportAPI_MVP {
    
    public function __construct() {
        add_action('rest_api_init', array($this, 'register_routes'));
        add_action('rest_api_init', array($this, 'add_cors_support'));
        add_action('admin_menu', array($this, 'add_admin_menu'));
        add_action('admin_enqueue_scripts', array($this, 'enqueue_admin_scripts'));
        add_action('wp_ajax_ai_tools_generate_api_key', array($this, 'ajax_generate_api_key'));
        add_action('wp_ajax_ai_tools_delete_api_key', array($this, 'ajax_delete_api_key'));
        
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
        
        require_once(ABSPATH . 'wp-admin/includes/upgrade.php');
        dbDelta($api_keys_sql);
        
        // 创建演示API Key
        if ($wpdb->get_var("SHOW TABLES LIKE '$api_keys_table'") == $api_keys_table) {
            $existing_keys = $wpdb->get_var("SELECT COUNT(*) FROM $api_keys_table");
            if ($existing_keys == 0) {
                $demo_key = 'ak_mvp_demo_' . bin2hex(random_bytes(20));
                $wpdb->insert($api_keys_table, array(
                    'api_key' => $demo_key,
                    'name' => 'MVP演示API Key',
                    'description' => 'MVP版本自动创建的演示API Key',
                    'rate_limit' => 100,
                    'status' => 'active',
                    'created_by' => 1,
                    'created_at' => current_time('mysql')
                ));
                update_option('ai_tools_mvp_demo_api_key', $demo_key);
            }
        }
        
        return true;
    }
    
    /**
     * 添加CORS支持
     */
    public function add_cors_support() {
        add_action('wp_loaded', function() {
            if (isset($_SERVER['REQUEST_METHOD']) && $_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
                if (strpos($_SERVER['REQUEST_URI'], '/wp-json/ai-tools/') !== false) {
                    header('Access-Control-Allow-Origin: *');
                    header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS');
                    header('Access-Control-Allow-Headers: X-API-Key, Authorization, Content-Type, Accept');
                    header('Access-Control-Max-Age: 86400');
                    exit;
                }
            }
        });
    }
    
    /**
     * 设置CORS头部
     */
    private function set_cors_headers($response) {
        $response->header('Access-Control-Allow-Origin', '*');
        $response->header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
        $response->header('Access-Control-Allow-Headers', 'X-API-Key, Authorization, Content-Type, Accept');
        $response->header('Access-Control-Expose-Headers', 'X-Total-Count, X-Total-Pages');
        return $response;
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
                'category' => array('sanitize_callback' => 'sanitize_text_field')
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

        register_rest_route('ai-tools/v1', '/tools/random', array(
            'methods' => 'GET',
            'callback' => array($this, 'get_random_tools'),
            'permission_callback' => array($this, 'check_api_key'),
            'args' => array(
                'count' => array('default' => 5, 'sanitize_callback' => 'absint')
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

        // 导入端点 - 关键的导入功能
        register_rest_route('ai-tools/v1', '/import', array(
            'methods' => 'POST',
            'callback' => array($this, 'import_tool'),
            'permission_callback' => array($this, 'check_api_key'),
            'args' => array(
                'tool_data' => array('required' => true),
                'post_id' => array('sanitize_callback' => 'absint'),
                'update_mode' => array('sanitize_callback' => 'rest_sanitize_boolean')
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
     * 获取AI工具列表
     */
    public function get_all_tools($request) {
        $page = $request->get_param('page') ?: 1;
        $per_page = min(max(1, intval($request->get_param('per_page'))), 100);
        $search = $request->get_param('search');
        $category = $request->get_param('category');
        
        $args = array(
            'post_type' => 'aihub',
            'post_status' => 'publish',
            'posts_per_page' => $per_page,
            'paged' => $page,
            'orderby' => 'date',
            'order' => 'DESC'
        );
        
        // 搜索
        if (!empty($search)) {
            $args['s'] = sanitize_text_field($search);
        }
        
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
        
        $query = new WP_Query($args);
        $tools = array();
        
        if ($query->have_posts()) {
            while ($query->have_posts()) {
                $query->the_post();
                $post_id = get_the_ID();
                
                $tool_data = $this->_build_tool_data_mvp($post_id);
                if ($tool_data) {
                    $tools[] = $tool_data;
                }
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
        
        return $this->set_cors_headers($response);
    }
    
    /**
     * 获取单个工具详情
     */
    public function get_single_tool($request) {
        $tool_id = intval($request->get_param('id'));
        
        $tool_data = $this->_build_tool_data_mvp($tool_id);
        
        if (!$tool_data) {
            $response = new WP_REST_Response(array(
                'success' => false,
                'message' => '工具不存在',
                'code' => 'not_found'
            ), 404);
            return $this->set_cors_headers($response);
        }
        
        $response = new WP_REST_Response(array(
            'success' => true,
            'data' => $tool_data,
            'timestamp' => current_time('c')
        ), 200);
        
        return $this->set_cors_headers($response);
    }

    /**
     * 获取随机工具
     */
    public function get_random_tools($request) {
        $count = min(max(1, intval($request->get_param('count'))), 20);
        
        $args = array(
            'post_type' => 'aihub',
            'post_status' => 'publish',
            'posts_per_page' => $count,
            'orderby' => 'rand'
        );
        
        $query = new WP_Query($args);
        $tools = array();
        
        if ($query->have_posts()) {
            while ($query->have_posts()) {
                $query->the_post();
                $post_id = get_the_ID();
                
                $tool_data = $this->_build_tool_data_mvp($post_id);
                if ($tool_data) {
                    $tools[] = $tool_data;
                }
            }
        }
        wp_reset_postdata();
        
        $response = new WP_REST_Response(array(
            'success' => true,
            'data' => $tools,
            'count' => count($tools),
            'timestamp' => current_time('c')
        ), 200);
        
        return $this->set_cors_headers($response);
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
                
                $tool_data = $this->_build_tool_data_mvp($post_id);
                if ($tool_data) {
                    $tools[] = $tool_data;
                }
            }
        }
        wp_reset_postdata();
        
        $response = new WP_REST_Response(array(
            'success' => true,
            'data' => $tools,
            'count' => count($tools),
            'timestamp' => current_time('c')
        ), 200);
        
        return $this->set_cors_headers($response);
    }
    
    /**
     * 测试连接
     */
    public function test_connection($request) {
        $response = new WP_REST_Response(array(
            'success' => true,
            'message' => 'MVP版本API连接成功',
            'version' => '3.0-MVP',
            'timestamp' => current_time('c')
        ), 200);
        
        return $this->set_cors_headers($response);
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
    
    /**
     * 生成API Key
     */
    public function generate_api_key($request) {
        $name = sanitize_text_field($request->get_param('name'));
        $description = sanitize_textarea_field($request->get_param('description') ?: '');
        $rate_limit = intval($request->get_param('rate_limit')) ?: 1000;
        
        if (empty($name)) {
            $response = new WP_REST_Response(array(
                'success' => false,
                'message' => '名称不能为空'
            ), 400);
            return $this->set_cors_headers($response);
        }
        
        // 生成API Key
        $api_key = 'ak_mvp_' . bin2hex(random_bytes(24));
        
        global $wpdb;
        $table_name = $wpdb->prefix . 'ai_tools_api_keys';
        
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
            $response = new WP_REST_Response(array(
                'success' => false,
                'message' => '创建API Key失败: ' . $wpdb->last_error
            ), 500);
            return $this->set_cors_headers($response);
        }
        
        $response = new WP_REST_Response(array(
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
        
        return $this->set_cors_headers($response);
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
        
        $response = new WP_REST_Response(array(
            'success' => true,
            'data' => $keys
        ), 200);
        
        return $this->set_cors_headers($response);
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
            $response = new WP_REST_Response(array(
                'success' => false,
                'message' => '删除失败'
            ), 500);
            return $this->set_cors_headers($response);
        }
        
        $response = new WP_REST_Response(array(
            'success' => true,
            'message' => 'API Key已删除'
        ), 200);
        
        return $this->set_cors_headers($response);
    }
    
    /**
     * 导入AI工具 - MVP版本的核心导入功能
     */
    public function import_tool($request) {
        $tool_data = $request->get_param('tool_data');
        $post_id = $request->get_param('post_id');
        $update_mode = $request->get_param('update_mode');
        
        if (empty($tool_data) || !is_array($tool_data)) {
            $response = new WP_REST_Response(array(
                'success' => false,
                'message' => '工具数据不能为空'
            ), 400);
            return $this->set_cors_headers($response);
        }
        
        $product_name = $tool_data['product_name'] ?? 'Unknown Tool';
        
        // Gemini增强（如果可用）
        $tool_data = $this->_enhance_tool_data_if_available($tool_data);
        
        try {
            if ($update_mode && $post_id) {
                // 更新现有工具
                $result = $this->_update_tool_mvp($post_id, $tool_data);
            } else {
                // 创建新工具
                $result = $this->_create_tool_mvp($tool_data);
            }
            
            if ($result['success']) {
                $response = new WP_REST_Response(array(
                    'success' => true,
                    'message' => $result['message'],
                    'post_id' => $result['post_id'],
                    'tool_name' => $product_name,
                    'updated' => $update_mode && $post_id
                ), 200);
            } else {
                $response = new WP_REST_Response(array(
                    'success' => false,
                    'message' => $result['message'],
                    'error' => $result['error'] ?? ''
                ), 500);
            }
            
        } catch (Exception $e) {
            $response = new WP_REST_Response(array(
                'success' => false,
                'message' => '导入过程中发生错误',
                'error' => $e->getMessage()
            ), 500);
        }
        
        return $this->set_cors_headers($response);
    }
    
    /**
     * 增强工具数据（如果Gemini可用）
     */
    private function _enhance_tool_data_if_available($tool_data) {
        try {
            // 执行PHP版本的增强逻辑
            $enhanced_data = $this->_enhance_with_gemini_logic($tool_data);
            error_log("MVP: PHP增强完成 - " . $tool_data['product_name']);
            return $enhanced_data;
        } catch (Exception $e) {
            error_log("MVP: PHP增强失败 - " . $e->getMessage());
            return $tool_data;
        }
    }
    
    /**
     * 简化的Gemini增强逻辑（PHP版本）
     */
    private function _enhance_with_gemini_logic($tool_data) {
        $product_name = $tool_data['product_name'] ?? '';
        $category = $tool_data['category'] ?? '';
        
        // 增强基础字段 - 强制设置
        $tool_data['author_company'] = $this->_guess_company_name($product_name);
        $tool_data['primary_task'] = $this->_guess_primary_task($category);
        $tool_data['initial_release_date'] = '2023';
        $tool_data['message'] = "Try " . $product_name;
        
        // 增强功能特性 - 强制设置
        $tool_data['features'] = $this->_generate_default_features($category);
        $tool_data['featured_matches'] = $this->_generate_featured_matches($category);
        $tool_data['other_tools'] = $this->_generate_other_tools($category);
        
        // 增强FAQ - 强制设置
        $tool_data['faq'] = $this->_generate_default_faq($product_name, $category);
        
        // 增强优缺点
        if (empty($tool_data['pros_list'])) {
            $tool_data['pros_list'] = $this->_generate_default_pros($category);
        }
        
        if (empty($tool_data['cons_list'])) {
            $tool_data['cons_list'] = $this->_generate_default_cons($category);
        }
        
        return $tool_data;
    }
    
    /**
     * 猜测公司名称
     */
    private function _guess_company_name($product_name) {
        $common_companies = array(
            'ChatGPT' => 'OpenAI',
            'Claude' => 'Anthropic',
            'Gemini' => 'Google',
            'Copilot' => 'Microsoft',
            'Midjourney' => 'Midjourney Inc.',
            'DALL-E' => 'OpenAI',
            'Stable Diffusion' => 'Stability AI'
        );
        
        foreach ($common_companies as $tool => $company) {
            if (stripos($product_name, $tool) !== false) {
                return $company;
            }
        }
        
        return ucfirst(strtolower($product_name)) . ' Team';
    }
    
    /**
     * 猜测主要任务
     */
    private function _guess_primary_task($category) {
        $task_mapping = array(
            'AI Writing Assistant' => 'Text Generation',
            'AI Image Generator' => 'Image Creation',
            'AI Code Assistant' => 'Code Generation',
            'AI Search Engine' => 'Search & Discovery',
            'AI Chatbot' => 'Conversation',
            'AI Video Generator' => 'Video Creation',
            'AI Audio Generator' => 'Audio Creation'
        );
        
        return $task_mapping[$category] ?? 'AI Processing';
    }
    
    /**
     * 生成默认功能特性
     */
    private function _generate_default_features($category) {
        $features_by_category = array(
            'AI Writing Assistant' => array(
                'Natural language processing',
                'Grammar and style checking',
                'Content generation',
                'Multiple language support',
                'Real-time suggestions'
            ),
            'AI Image Generator' => array(
                'Text-to-image generation',
                'Style customization',
                'High-resolution output',
                'Batch processing',
                'Multiple art styles'
            ),
            'AI Search Engine' => array(
                'Visual search capabilities',
                'Advanced filtering',
                'Real-time results',
                'Multi-format support',
                'Intelligent recommendations'
            )
        );
        
        return $features_by_category[$category] ?? array(
            'AI-powered processing',
            'User-friendly interface',
            'Fast performance',
            'Reliable results',
            'Easy integration'
        );
    }
    
    /**
     * 生成推荐工具
     */
    private function _generate_featured_matches($category) {
        $matches_by_category = array(
            'AI Writing Assistant' => array('Grammarly', 'Notion AI', 'Jasper'),
            'AI Image Generator' => array('Photoshop', 'Canva', 'Figma'),
            'AI Search Engine' => array('Google Lens', 'TinEye', 'Pinterest Lens')
        );
        
        return $matches_by_category[$category] ?? array('Similar Tool 1', 'Similar Tool 2', 'Similar Tool 3');
    }
    
    /**
     * 生成其他工具
     */
    private function _generate_other_tools($category) {
        $tools_by_category = array(
            'AI Writing Assistant' => array('ChatGPT', 'Claude', 'Jasper', 'Copy.ai'),
            'AI Image Generator' => array('DALL-E', 'Midjourney', 'Stable Diffusion', 'Adobe Firefly'),
            'AI Search Engine' => array('Perplexity', 'You.com', 'Bing AI', 'Phind')
        );
        
        return $tools_by_category[$category] ?? array('Alternative 1', 'Alternative 2', 'Alternative 3', 'Alternative 4');
    }
    
    /**
     * 生成默认FAQ
     */
    private function _generate_default_faq($product_name, $category) {
        return array(
            array(
                'question' => "What is {$product_name}?",
                'answer' => "{$product_name} is an {$category} tool that helps users with AI-powered tasks."
            ),
            array(
                'question' => "How do I use {$product_name}?",
                'answer' => "Simply visit the website, create an account if needed, and start using the {$category} features."
            ),
            array(
                'question' => "Is {$product_name} free?",
                'answer' => "{$product_name} may offer both free and premium plans. Check their pricing page for details."
            ),
            array(
                'question' => "What are the main features?",
                'answer' => "{$product_name} offers advanced {$category} capabilities with user-friendly interface and reliable performance."
            ),
            array(
                'question' => "Who should use {$product_name}?",
                'answer' => "{$product_name} is suitable for professionals, students, and anyone who needs {$category} assistance."
            )
        );
    }
    
    /**
     * 构建MVP版本的工具数据 - 从6个JSON字段重新组合成扁平化结构
     */
    private function _build_tool_data_mvp($post_id, $post = null) {
        if (!$post) {
            $post = get_post($post_id);
        }
        
        if (!$post || $post->post_type !== 'aihub' || $post->post_status !== 'publish') {
            return null;
        }
        
        // 获取6个JSON字段 - 增强版读取
        $basic_info_raw = get_post_meta($post_id, 'basic_info', true);
        $media_data_raw = get_post_meta($post_id, 'media_data', true);
        $ratings_data_raw = get_post_meta($post_id, 'ratings_data', true);
        $ui_text_data_raw = get_post_meta($post_id, 'ui_text_data', true);
        $features_data_raw = get_post_meta($post_id, 'features_data', true);
        $complex_data_raw = get_post_meta($post_id, 'complex_data', true);
        
        error_log("MVP读取: basic_info长度=" . strlen($basic_info_raw) . ", media_data长度=" . strlen($media_data_raw));
        
        // 解析JSON字段
        $basic_info = $this->_parse_json_field($basic_info_raw);
        $media_data = $this->_parse_json_field($media_data_raw);
        $ratings_data = $this->_parse_json_field($ratings_data_raw);
        $ui_text_data = $this->_parse_json_field($ui_text_data_raw);
        $features_data = $this->_parse_json_field($features_data_raw);
        $complex_data = $this->_parse_json_field($complex_data_raw);
        
        error_log("MVP解析: basic_info字段数=" . count($basic_info) . ", media_data字段数=" . count($media_data));
        
        // 检查是否有任何JSON数据（只要有一个字段有数据就使用MVP模式）
        $has_json_data = !empty($basic_info) || !empty($media_data) || !empty($ratings_data) || 
                        !empty($ui_text_data) || !empty($features_data) || !empty($complex_data);
        
        if (!$has_json_data) {
            error_log("MVP: 没有JSON数据，使用回退模式");
            return $this->_build_tool_data_fallback($post_id, $post);
        }
        
        error_log("MVP: 使用JSON数据模式");
        
        // 获取分类和标签
        $categories = wp_get_post_terms($post_id, 'category', array('fields' => 'names'));
        $tags = wp_get_post_terms($post_id, 'post_tag', array('fields' => 'names'));
        
        // 构建扁平化的完整数据结构
        $tool_data = array(
            // WordPress基础信息
            'id' => $post_id,
            'title' => $post->post_title,
            'slug' => $post->post_name,
            'content' => $post->post_content,
            'excerpt' => $post->post_excerpt,
            'url' => get_permalink($post_id),
            'date_created' => get_the_date('c', $post_id),
            'date_modified' => get_the_modified_date('c', $post_id),
            
            // 基础信息 (basic_info)
            'product_name' => $basic_info['product_name'] ?? $post->post_title,
            'product_url' => $basic_info['product_url'] ?? '',
            'short_introduction' => $basic_info['short_introduction'] ?? $post->post_excerpt,
            'product_story' => $basic_info['product_story'] ?? $post->post_content,
            'author_company' => $basic_info['author_company'] ?? '',
            'primary_task' => $basic_info['primary_task'] ?? '',
            'category' => $basic_info['category'] ?? (isset($categories[0]) ? $categories[0] : ''),
            'original_category_name' => $basic_info['original_category_name'] ?? '',
            'initial_release_date' => $basic_info['initial_release_date'] ?? '',
            'general_price_tag' => $basic_info['general_price_tag'] ?? 'Unknown',
            
            // 媒体资源 (media_data)
            'logo_img_url' => $media_data['logo_img_url'] ?? '',
            'overview_img_url' => $media_data['overview_img_url'] ?? '',
            'demo_video_url' => $media_data['demo_video_url'] ?? '',
            
            // 评分数据 (ratings_data)
            'average_rating' => floatval($ratings_data['average_rating'] ?? 0),
            'popularity_score' => floatval($ratings_data['popularity_score'] ?? 0),
            'user_ratings_count' => intval($ratings_data['user_ratings_count'] ?? 0),
            'is_verified_tool' => boolval($ratings_data['is_verified_tool'] ?? false),
            'number_of_tools_by_author' => intval($ratings_data['number_of_tools_by_author'] ?? 0),
            
            // UI文本数据 (ui_text_data) - 所有15个字段
            'message' => $ui_text_data['message'] ?? '',
            'copy_url_text' => $ui_text_data['copy_url_text'] ?? '',
            'save_button_text' => $ui_text_data['save_button_text'] ?? '',
            'vote_best_ai_tool_text' => $ui_text_data['vote_best_ai_tool_text'] ?? '',
            'how_would_you_rate_text' => $ui_text_data['how_would_you_rate_text'] ?? '',
            'help_other_people_text' => $ui_text_data['help_other_people_text'] ?? '',
            'your_rating_text' => $ui_text_data['your_rating_text'] ?? '',
            'post_review_button_text' => $ui_text_data['post_review_button_text'] ?? '',
            'feature_requests_intro' => $ui_text_data['feature_requests_intro'] ?? '',
            'request_feature_button_text' => $ui_text_data['request_feature_button_text'] ?? '',
            'view_more_pros_text' => $ui_text_data['view_more_pros_text'] ?? '',
            'view_more_cons_text' => $ui_text_data['view_more_cons_text'] ?? '',
            'alternatives_count_text' => $ui_text_data['alternatives_count_text'] ?? '',
            'view_more_alternatives_text' => $ui_text_data['view_more_alternatives_text'] ?? '',
            'if_you_liked_text' => $ui_text_data['if_you_liked_text'] ?? '',
            'faq' => $ui_text_data['faq'] ?? array(),
            
            // 功能特性数据 (features_data)
            'inputs' => $features_data['inputs'] ?? array(),
            'outputs' => $features_data['outputs'] ?? array(),
            'features' => $features_data['features'] ?? array(),
            'pros_list' => $features_data['pros_list'] ?? array(),
            'cons_list' => $features_data['cons_list'] ?? array(),
            'related_tasks' => $features_data['related_tasks'] ?? array(),
            'alternative_tools' => $features_data['alternative_tools'] ?? array(),
            'featured_matches' => $features_data['featured_matches'] ?? array(),
            'other_tools' => $features_data['other_tools'] ?? array(),
            
            // 复杂数据 (complex_data)
            'pricing_details' => $complex_data['pricing_details'] ?? array(),
            'releases' => $complex_data['releases'] ?? array(),
            'job_impacts' => $complex_data['job_impacts'] ?? array(),
            'alternatives' => $complex_data['alternatives'] ?? array(),
            
            // 分类和标签
            'categories' => is_array($categories) ? $categories : array(),
            'tags' => is_array($tags) ? $tags : array()
        );
        
        return $tool_data;
    }
    
    /**
     * 解析JSON字段
     */
    private function _parse_json_field($field_value) {
        if (empty($field_value)) {
            return array();
        }
        
        if (is_array($field_value)) {
            return $field_value;
        }
        
        if (is_string($field_value)) {
            $parsed = json_decode($field_value, true);
            return is_array($parsed) ? $parsed : array();
        }
        
        return array();
    }
    
    /**
     * 回退方法：使用传统ACF字段（兼容旧数据）
     */
    private function _build_tool_data_fallback($post_id, $post) {
        $fields = get_fields($post_id);
        
        if (empty($fields)) {
            return null;
        }
        
        // 获取分类和标签
        $categories = wp_get_post_terms($post_id, 'category', array('fields' => 'names'));
        $tags = wp_get_post_terms($post_id, 'post_tag', array('fields' => 'names'));
        
        // 基础的回退数据结构
        return array(
            'id' => $post_id,
            'title' => $post->post_title,
            'slug' => $post->post_name,
            'content' => $post->post_content,
            'excerpt' => $post->post_excerpt,
            'url' => get_permalink($post_id),
            'date_created' => get_the_date('c', $post_id),
            'date_modified' => get_the_modified_date('c', $post_id),
            'product_name' => $fields['product_name'] ?? $post->post_title,
            'product_url' => $fields['product_url'] ?? '',
            'short_introduction' => $fields['short_introduction'] ?? $post->post_excerpt,
            'author_company' => $fields['author_company'] ?? '',
            'logo_img_url' => $fields['logo_img_url'] ?? '',
            'average_rating' => floatval($fields['average_rating'] ?? 0),
            'popularity_score' => floatval($fields['popularity_score'] ?? 0),
            'general_price_tag' => $fields['general_price_tag'] ?? 'Unknown',
            'category' => isset($categories[0]) ? $categories[0] : '',
            'categories' => is_array($categories) ? $categories : array(),
            'tags' => is_array($tags) ? $tags : array(),
            // 其他字段设置为默认值
            'inputs' => array(),
            'outputs' => array(),
            'features' => array()
        );
    }
    
    /**
     * 创建新工具 - MVP版本
     */
    private function _create_tool_mvp($tool_data) {
        $product_name = $tool_data['product_name'] ?? 'Unknown Tool';
        
        // 准备文章数据
        $post_data = array(
            'post_title' => $product_name,
            'post_content' => $tool_data['product_story'] ?? $tool_data['short_introduction'] ?? '',
            'post_excerpt' => $tool_data['short_introduction'] ?? '',
            'post_status' => 'publish',
            'post_type' => 'aihub'
        );
        
        // 创建文章
        $post_id = wp_insert_post($post_data);
        
        if (is_wp_error($post_id)) {
            return array(
                'success' => false,
                'message' => '创建文章失败',
                'error' => $post_id->get_error_message()
            );
        }
        
        // 保存MVP版本的6个JSON字段
        $this->_save_acf_fields_mvp($post_id, $tool_data);
        
        // 设置分类和标签
        $this->_set_tool_taxonomy_mvp($post_id, $tool_data);
        
        return array(
            'success' => true,
            'message' => '工具创建成功',
            'post_id' => $post_id
        );
    }
    
    /**
     * 更新现有工具 - MVP版本
     */
    private function _update_tool_mvp($post_id, $tool_data) {
        $product_name = $tool_data['product_name'] ?? 'Unknown Tool';
        
        // 检查文章是否存在
        $post = get_post($post_id);
        if (!$post || $post->post_type !== 'aihub') {
            return array(
                'success' => false,
                'message' => '文章不存在或类型不正确'
            );
        }
        
        // 更新文章数据
        $post_data = array(
            'ID' => $post_id,
            'post_title' => $product_name,
            'post_content' => $tool_data['product_story'] ?? $tool_data['short_introduction'] ?? '',
            'post_excerpt' => $tool_data['short_introduction'] ?? ''
        );
        
        $result = wp_update_post($post_data);
        
        if (is_wp_error($result)) {
            return array(
                'success' => false,
                'message' => '更新文章失败',
                'error' => $result->get_error_message()
            );
        }
        
        // 更新MVP版本的6个JSON字段
        $this->_save_acf_fields_mvp($post_id, $tool_data);
        
        // 更新分类和标签
        $this->_set_tool_taxonomy_mvp($post_id, $tool_data);
        
        return array(
            'success' => true,
            'message' => '工具更新成功',
            'post_id' => $post_id
        );
    }
    
    /**
     * 保存ACF字段为6个JSON结构 - MVP核心方法
     */
    private function _save_acf_fields_mvp($post_id, $tool_data) {
        error_log("MVP: 开始保存ACF字段到文章 ID: $post_id");
        
        // 1. 基本信息 (basic_info)
        $basic_info = array(
            'product_name' => $tool_data['product_name'] ?? '',
            'product_url' => $tool_data['product_url'] ?? '',
            'short_introduction' => $tool_data['short_introduction'] ?? '',
            'product_story' => $tool_data['product_story'] ?? '',
            'author_company' => $tool_data['author_company'] ?? '',
            'primary_task' => $tool_data['primary_task'] ?? '',
            'category' => $tool_data['category'] ?? '',
            'original_category_name' => $tool_data['original_category_name'] ?? '',
            'initial_release_date' => $tool_data['initial_release_date'] ?? ''
        );
        
        // 2. 媒体数据 (media_data)
        $media_data = array(
            'logo_img_url' => $tool_data['logo_img_url'] ?? '',
            'overview_img_url' => $tool_data['overview_img_url'] ?? '',
            'demo_video_url' => $tool_data['demo_video_url'] ?? ''
        );
        
        // 3. 评分数据 (ratings_data)
        $ratings_data = array(
            'average_rating' => $tool_data['average_rating'] ?? 0,
            'popularity_score' => $tool_data['popularity_score'] ?? 0,
            'user_ratings_count' => $tool_data['user_ratings_count'] ?? 0,
            'is_verified_tool' => $tool_data['is_verified_tool'] ?? false,
            'number_of_tools_by_author' => $tool_data['number_of_tools_by_author'] ?? 0,
            'general_price_tag' => $tool_data['general_price_tag'] ?? 'Unknown'
        );
        
        // 4. UI文本数据 (ui_text_data)
        $ui_text_data = array(
            'message' => $tool_data['message'] ?? '',
            'copy_url_text' => $tool_data['copy_url_text'] ?? '',
            'save_button_text' => $tool_data['save_button_text'] ?? '',
            'vote_best_ai_tool_text' => $tool_data['vote_best_ai_tool_text'] ?? '',
            'how_would_you_rate_text' => $tool_data['how_would_you_rate_text'] ?? '',
            'help_other_people_text' => $tool_data['help_other_people_text'] ?? '',
            'your_rating_text' => $tool_data['your_rating_text'] ?? '',
            'post_review_button_text' => $tool_data['post_review_button_text'] ?? '',
            'feature_requests_intro' => $tool_data['feature_requests_intro'] ?? '',
            'request_feature_button_text' => $tool_data['request_feature_button_text'] ?? '',
            'view_more_pros_text' => $tool_data['view_more_pros_text'] ?? '',
            'view_more_cons_text' => $tool_data['view_more_cons_text'] ?? '',
            'alternatives_count_text' => $tool_data['alternatives_count_text'] ?? '',
            'view_more_alternatives_text' => $tool_data['view_more_alternatives_text'] ?? '',
            'if_you_liked_text' => $tool_data['if_you_liked_text'] ?? '',
            'faq' => $tool_data['faq'] ?? array()
        );
        
        // 5. 功能特性数据 (features_data)
        $features_data = array(
            'inputs' => $tool_data['inputs'] ?? array(),
            'outputs' => $tool_data['outputs'] ?? array(),
            'features' => $tool_data['features'] ?? array(),
            'pros_list' => $tool_data['pros_list'] ?? array(),
            'cons_list' => $tool_data['cons_list'] ?? array(),
            'related_tasks' => $tool_data['related_tasks'] ?? array(),
            'alternative_tools' => $tool_data['alternative_tools'] ?? array(),
            'featured_matches' => $tool_data['featured_matches'] ?? array(),
            'other_tools' => $tool_data['other_tools'] ?? array()
        );
        
        // 6. 复杂数据 (complex_data)
        $complex_data = array(
            'pricing_details' => $tool_data['pricing_details'] ?? array(),
            'releases' => $tool_data['releases'] ?? array(),
            'job_impacts' => $tool_data['job_impacts'] ?? array(),
            'alternatives' => $tool_data['alternatives'] ?? array()
        );
        
        // 准备要保存的6个JSON字段
        $json_fields = array(
            'basic_info' => $basic_info,
            'media_data' => $media_data,
            'ratings_data' => $ratings_data,
            'ui_text_data' => $ui_text_data,
            'features_data' => $features_data,
            'complex_data' => $complex_data
        );
        
        // 保存每个JSON字段，使用增强的保存机制
        foreach ($json_fields as $field_name => $field_data) {
            $json_string = json_encode($field_data, JSON_UNESCAPED_UNICODE);
            
            error_log("MVP: 开始保存字段 $field_name, 数据长度: " . strlen($json_string));
            
            // 检查JSON编码是否成功
            if (json_last_error() !== JSON_ERROR_NONE) {
                error_log("MVP: JSON编码失败 $field_name: " . json_last_error_msg());
                continue;
            }
            
            // 方法1: 直接使用 update_post_meta (最可靠)
            $meta_result = update_post_meta($post_id, $field_name, $json_string);
            error_log("MVP: update_post_meta $field_name: " . ($meta_result !== false ? 'success' : 'failed'));
            
            // 方法2: 使用 update_field (如果ACF可用)
            $acf_result = false;
            if (function_exists('update_field')) {
                $acf_result = update_field($field_name, $json_string, $post_id);
                error_log("MVP: update_field $field_name: " . ($acf_result ? 'success' : 'failed'));
            }
            
            // 方法3: 尝试获取ACF字段的实际key并使用
            if (function_exists('acf_get_field')) {
                $field_object = acf_get_field($field_name);
                if ($field_object && isset($field_object['key'])) {
                    $field_key = $field_object['key'];
                    $key_result = update_field($field_key, $json_string, $post_id);
                    error_log("MVP: update_field(实际key: $field_key) $field_name: " . ($key_result ? 'success' : 'failed'));
                } else {
                    error_log("MVP: 无法获取字段 $field_name 的ACF key");
                }
            }
            
            // 验证保存结果
            $saved_meta = get_post_meta($post_id, $field_name, true);
            $saved_field = function_exists('get_field') ? get_field($field_name, $post_id) : null;
            
            if (!empty($saved_meta)) {
                error_log("MVP: ✅ 字段 $field_name 通过meta保存成功，长度: " . strlen($saved_meta));
            } elseif (!empty($saved_field)) {
                error_log("MVP: ✅ 字段 $field_name 通过ACF保存成功，长度: " . strlen($saved_field));
            } else {
                error_log("MVP: ❌ 字段 $field_name 保存失败，尝试最后的强制保存");
                // 最后尝试：删除后重新添加
                delete_post_meta($post_id, $field_name);
                $force_result = add_post_meta($post_id, $field_name, $json_string, true);
                error_log("MVP: 强制保存 $field_name: " . ($force_result ? 'success' : 'failed'));
            }
        }
        
        error_log("MVP: ACF字段保存完成");
    }
    
    /**
     * 设置工具分类和标签 - MVP版本
     */
    private function _set_tool_taxonomy_mvp($post_id, $tool_data) {
        // 设置分类
        if (isset($tool_data['category']) && !empty($tool_data['category'])) {
            $category_term = get_term_by('name', $tool_data['category'], 'category');
            if (!$category_term) {
                // 创建分类
                $category_result = wp_insert_term($tool_data['category'], 'category');
                if (!is_wp_error($category_result)) {
                    $category_term = get_term($category_result['term_id'], 'category');
                }
            }
            
            if ($category_term) {
                wp_set_post_terms($post_id, array($category_term->term_id), 'category');
            }
        }
        
        // 设置标签
        if (isset($tool_data['tags']) && is_array($tool_data['tags'])) {
            wp_set_post_tags($post_id, $tool_data['tags']);
        }
    }
    
    /**
     * AJAX生成API Key
     */
    public function ajax_generate_api_key() {
        check_ajax_referer('ai_tools_api_nonce', 'nonce');
        
        if (!current_user_can('manage_options')) {
            wp_die('权限不足');
        }
        
        $name = sanitize_text_field($_POST['name']);
        $description = sanitize_textarea_field($_POST['description']);
        $rate_limit = intval($_POST['rate_limit']) ?: 1000;
        
        if (empty($name)) {
            wp_send_json_error('名称不能为空');
        }
        
        $api_key = 'ak_mvp_' . bin2hex(random_bytes(24));
        
        global $wpdb;
        $table_name = $wpdb->prefix . 'ai_tools_api_keys';
        
        $result = $wpdb->insert($table_name, array(
            'api_key' => $api_key,
            'name' => $name,
            'description' => $description,
            'rate_limit' => $rate_limit,
            'status' => 'active',
            'created_by' => get_current_user_id(),
            'created_at' => current_time('mysql')
        ));
        
        if ($result) {
            wp_send_json_success(array(
                'api_key' => $api_key,
                'name' => $name
            ));
        } else {
            wp_send_json_error('创建失败');
        }
    }
    
    /**
     * AJAX删除API Key
     */
    public function ajax_delete_api_key() {
        check_ajax_referer('ai_tools_api_nonce', 'nonce');
        
        if (!current_user_can('manage_options')) {
            wp_die('权限不足');
        }
        
        $key_id = intval($_POST['key_id']);
        
        global $wpdb;
        $table_name = $wpdb->prefix . 'ai_tools_api_keys';
        
        $result = $wpdb->delete($table_name, array('id' => $key_id), array('%d'));
        
        if ($result) {
            wp_send_json_success();
        } else {
            wp_send_json_error('删除失败');
        }
    }
    
    /**
     * 加载管理页面脚本
     */
    public function enqueue_admin_scripts($hook) {
        if ($hook !== 'tools_page_ai-tools-api-mvp') {
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
     * 添加管理菜单
     */
    public function add_admin_menu() {
        add_management_page(
            'AI工具API - MVP版',
            'AI工具API MVP',
            'manage_options',
            'ai-tools-api-mvp',
            array($this, 'admin_page')
        );
    }
    
    /**
     * 管理页面
     */
    public function admin_page() {
        global $wpdb;
        
        $table_name = $wpdb->prefix . 'ai_tools_api_keys';
        
        // 确保表存在
        if (!$wpdb->get_var("SHOW TABLES LIKE '$table_name'")) {
            $this->create_api_tables();
        }
        
        $api_keys = $wpdb->get_results("SELECT * FROM $table_name ORDER BY created_at DESC");
        $demo_key = get_option('ai_tools_mvp_demo_api_key', '');
        
        ?>
        <style>
        .ai-tools-stats {
            display: flex;
            gap: 20px;
            margin: 20px 0;
        }
        .stats-card {
            background: #fff;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 20px;
            min-width: 120px;
            text-align: center;
        }
        .stats-card h3 {
            margin: 0 0 10px;
            font-size: 14px;
            color: #666;
        }
        .stats-number {
            font-size: 32px;
            font-weight: bold;
            color: #0073aa;
        }
        .ai-tools-generate-form {
            background: #fff;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 20px;
            margin: 20px 0;
        }
        .ai-tools-modal {
            display: none;
            position: fixed;
            z-index: 9999;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.4);
        }
        .modal-content {
            background-color: #fefefe;
            margin: 15% auto;
            padding: 20px;
            border: 1px solid #888;
            width: 500px;
            border-radius: 5px;
        }
        .close {
            color: #aaa;
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }
        .demo-key-notice {
            background: #e7f3ff;
            border: 1px solid #b8daff;
            border-radius: 5px;
            padding: 15px;
            margin: 20px 0;
        }
        </style>
        
        <div class="wrap">
            <h1>🤖 AI工具API - MVP版本</h1>
            <div class="notice notice-info">
                <p><strong>MVP版本特性：</strong>使用6个JSON字段存储数据，输出扁平化结构，需要API Key认证</p>
            </div>
            
            <?php if ($demo_key): ?>
            <div class="demo-key-notice">
                <h3>🎯 演示API Key</h3>
                <p>系统已自动创建演示API Key：<code><?php echo esc_html($demo_key); ?></code></p>
                <p>您可以使用此Key测试API功能，或创建新的API Key。</p>
            </div>
            <?php endif; ?>
            
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
                            <td><input type="text" id="api_key_name" name="name" class="regular-text" required placeholder="例如：前端应用" /></td>
                        </tr>
                        <tr>
                            <th><label for="api_key_description">描述</label></th>
                            <td><textarea id="api_key_description" name="description" class="large-text" rows="3" placeholder="可选：描述此API Key的用途"></textarea></td>
                        </tr>
                        <tr>
                            <th><label for="api_key_rate_limit">请求限制（每天）</label></th>
                            <td><input type="number" id="api_key_rate_limit" name="rate_limit" value="1000" min="1" max="10000" /></td>
                        </tr>
                    </table>
                    <p class="submit">
                        <input type="submit" name="submit" class="button-primary" value="生成API Key" />
                        <span class="spinner"></span>
                    </p>
                </form>
            </div>
            
            <!-- API Key列表 -->
            <h2>🔑 API Key列表</h2>
            <?php if (empty($api_keys)): ?>
                <p>暂无API Key，请先生成一个。</p>
            <?php else: ?>
                <table class="wp-list-table widefat fixed striped">
                    <thead>
                        <tr>
                            <th style="width: 150px;">名称</th>
                            <th style="width: 200px;">API Key</th>
                            <th>描述</th>
                            <th style="width: 80px;">状态</th>
                            <th style="width: 100px;">请求限制</th>
                            <th style="width: 120px;">创建时间</th>
                            <th style="width: 120px;">最后使用</th>
                            <th style="width: 100px;">操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ($api_keys as $key): ?>
                        <tr>
                            <td><strong><?php echo esc_html($key->name); ?></strong></td>
                            <td>
                                <code><?php echo esc_html(substr($key->api_key, 0, 12) . '...'); ?></code>
                                <button type="button" class="button-link show-full-key" data-full-key="<?php echo esc_attr($key->api_key); ?>">显示完整</button>
                            </td>
                            <td><?php echo esc_html($key->description ?: '-'); ?></td>
                            <td>
                                <span class="status-<?php echo $key->status; ?>">
                                    <?php echo $key->status === 'active' ? '✅ 活跃' : '❌ 停用'; ?>
                                </span>
                            </td>
                            <td><?php echo number_format($key->rate_limit); ?>/天</td>
                            <td><?php echo esc_html(date('Y-m-d H:i', strtotime($key->created_at))); ?></td>
                            <td><?php echo $key->last_used_at ? esc_html(date('Y-m-d H:i', strtotime($key->last_used_at))) : '从未使用'; ?></td>
                            <td>
                                <button type="button" class="button-link-delete delete-key" 
                                        data-key-id="<?php echo $key->id; ?>" 
                                        data-key-name="<?php echo esc_attr($key->name); ?>">删除</button>
                            </td>
                        </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            <?php endif; ?>
            
            <!-- API端点信息 -->
            <h2>🌐 API端点</h2>
            <table class="wp-list-table widefat fixed striped">
                <thead>
                    <tr>
                        <th>端点</th>
                        <th>方法</th>
                        <th>描述</th>
                        <th>认证</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><code>/wp-json/ai-tools/v1/tools</code></td>
                        <td>GET</td>
                        <td>获取工具列表</td>
                        <td>✅ 需要</td>
                    </tr>
                    <tr>
                        <td><code>/wp-json/ai-tools/v1/tools/{id}</code></td>
                        <td>GET</td>
                        <td>获取单个工具</td>
                        <td>✅ 需要</td>
                    </tr>
                    <tr>
                        <td><code>/wp-json/ai-tools/v1/tools/random</code></td>
                        <td>GET</td>
                        <td>获取随机工具</td>
                        <td>✅ 需要</td>
                    </tr>
                    <tr>
                        <td><code>/wp-json/ai-tools/v1/tools/popular</code></td>
                        <td>GET</td>
                        <td>获取热门工具</td>
                        <td>✅ 需要</td>
                    </tr>
                    <tr>
                        <td><code>/wp-json/ai-tools/v1/import</code></td>
                        <td>POST</td>
                        <td>导入工具数据</td>
                        <td>✅ 需要</td>
                    </tr>
                    <tr>
                        <td><code>/wp-json/ai-tools/v1/test</code></td>
                        <td>GET</td>
                        <td>测试连接</td>
                        <td>✅ 需要</td>
                    </tr>
                </tbody>
            </table>
            
            <!-- 数据结构说明 -->
            <h2>📊 数据结构</h2>
            <p>MVP版本将数据分为6个JSON字段存储，但API输出时会重新组合为完整的扁平化结构：</p>
            <ul>
                <li><strong>basic_info</strong>: 产品基本信息（名称、链接、公司等）</li>
                <li><strong>media_data</strong>: 媒体文件链接（Logo、图片、视频）</li>
                <li><strong>ratings_data</strong>: 评分和统计数据（评分、流行度等）</li>
                <li><strong>ui_text_data</strong>: 界面文本标签（15个UI文本字段）</li>
                <li><strong>features_data</strong>: 功能特性列表（输入输出、优缺点等）</li>
                <li><strong>complex_data</strong>: 复杂对象数据（定价、发布信息等）</li>
            </ul>
            
            <!-- 使用示例 -->
            <h2>💡 使用示例</h2>
            <h3>认证方式</h3>
            <pre><code>// 方式1：X-API-Key 头部（推荐）
fetch('/wp-json/ai-tools/v1/tools', {
    headers: {
        'X-API-Key': 'your_api_key_here'
    }
});

// 方式2：Authorization Bearer 头部
fetch('/wp-json/ai-tools/v1/tools', {
    headers: {
        'Authorization': 'Bearer your_api_key_here'
    }
});

// 方式3：URL参数
fetch('/wp-json/ai-tools/v1/tools?api_key=your_api_key_here');</code></pre>
            
            <h3>获取数据</h3>
            <pre><code>// 获取工具列表
const response = await fetch('/wp-json/ai-tools/v1/tools', {
    headers: { 'X-API-Key': 'your_api_key_here' }
});
const result = await response.json();

console.log(result.data); // 扁平化的工具数据数组
console.log(result.data[0].product_name); // 直接访问字段
console.log(result.data[0].inputs); // 数组字段
console.log(result.data[0].pricing_details); // 对象字段</code></pre>
        </div>
        
        <!-- API Key显示模态框 -->
        <div id="api-key-modal" class="ai-tools-modal">
            <div class="modal-content">
                <span class="close">&times;</span>
                <h2>完整API Key</h2>
                <p>请妥善保管您的API Key，不要在公开场所分享。</p>
                <input type="text" id="full-api-key" readonly style="width: 100%; padding: 8px; font-family: monospace;" />
                <p style="margin-top: 10px;">
                    <button type="button" class="button copy-api-key">复制</button>
                </p>
            </div>
        </div>
        <?php
    }
}

// 初始化MVP版本插件
new AIToolImportAPI_MVP();

/**
 * 激活插件时的处理
 */
register_activation_hook(__FILE__, function() {
    $plugin = new AIToolImportAPI_MVP();
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