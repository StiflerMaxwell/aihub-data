<?php
/**
 * Plugin Name: AI工具导入API
 * Description: 自定义API端点用于批量导入AI工具数据
 * Version: 1.0
 * Author: Maxwell
 */

// 防止直接访问
if (!defined('ABSPATH')) {
    exit;
}

class AIToolImportAPI {
    
    public function __construct() {
        add_action('rest_api_init', array($this, 'register_routes'));
    }
    
    /**
     * 注册自定义API路由
     */
    public function register_routes() {
        register_rest_route('ai-tools/v1', '/import', array(
            'methods' => 'POST',
            'callback' => array($this, 'import_single_tool'),
            'permission_callback' => array($this, 'check_permissions'),
            'args' => array(
                'tool_data' => array(
                    'required' => true,
                    'type' => 'object',
                    'description' => 'AI工具的完整数据'
                )
            )
        ));
        
        register_rest_route('ai-tools/v1', '/batch-import', array(
            'methods' => 'POST',
            'callback' => array($this, 'batch_import_tools'),
            'permission_callback' => array($this, 'check_permissions'),
            'args' => array(
                'tools' => array(
                    'required' => true,
                    'type' => 'array',
                    'description' => 'AI工具数据数组'
                )
            )
        ));
        
        register_rest_route('ai-tools/v1', '/test', array(
            'methods' => 'GET',
            'callback' => array($this, 'test_connection'),
            'permission_callback' => array($this, 'check_permissions')
        ));
    }
    
    /**
     * 检查权限
     */
    public function check_permissions() {
        return current_user_can('edit_posts') && current_user_can('upload_files');
    }
    
    /**
     * 测试连接
     */
    public function test_connection($request) {
        $user = wp_get_current_user();
        
        return new WP_REST_Response(array(
            'success' => true,
            'message' => 'API连接成功',
            'user' => array(
                'id' => $user->ID,
                'name' => $user->display_name,
                'email' => $user->user_email
            ),
            'timestamp' => current_time('mysql')
        ), 200);
    }
    
    /**
     * 导入单个AI工具
     */
    public function import_single_tool($request) {
        $tool_data = $request->get_param('tool_data');
        
        if (empty($tool_data)) {
            return new WP_REST_Response(array(
                'success' => false,
                'message' => '工具数据不能为空'
            ), 400);
        }
        
        $result = $this->process_single_tool($tool_data);
        
        if ($result['success']) {
            return new WP_REST_Response($result, 200);
        } else {
            return new WP_REST_Response($result, 500);
        }
    }
    
    /**
     * 批量导入AI工具
     */
    public function batch_import_tools($request) {
        $tools = $request->get_param('tools');
        
        if (empty($tools) || !is_array($tools)) {
            return new WP_REST_Response(array(
                'success' => false,
                'message' => '工具数据数组不能为空'
            ), 400);
        }
        
        $results = array();
        $success_count = 0;
        $error_count = 0;
        
        foreach ($tools as $index => $tool_data) {
            $result = $this->process_single_tool($tool_data);
            $results[] = array(
                'index' => $index,
                'tool_name' => $tool_data['product_name'] ?? 'Unknown',
                'success' => $result['success'],
                'message' => $result['message'],
                'post_id' => $result['post_id'] ?? null,
                'errors' => $result['errors'] ?? array()
            );
            
            if ($result['success']) {
                $success_count++;
            } else {
                $error_count++;
            }
            
            // 添加延迟避免服务器过载
            usleep(500000); // 0.5秒
        }
        
        return new WP_REST_Response(array(
            'success' => true,
            'summary' => array(
                'total' => count($tools),
                'success' => $success_count,
                'errors' => $error_count
            ),
            'results' => $results
        ), 200);
    }
    
    /**
     * 处理单个工具数据
     */
    private function process_single_tool($tool_data) {
        $errors = array();
        
        try {
            // 1. 验证必需字段
            if (empty($tool_data['product_name'])) {
                return array(
                    'success' => false,
                    'message' => '产品名称是必需的',
                    'errors' => array('product_name' => '产品名称不能为空')
                );
            }
            
            // 2. 检查是否已存在
            $existing_post = $this->find_existing_tool($tool_data['product_name'], $tool_data['product_url'] ?? '');
            
            if ($existing_post) {
                $post_id = $existing_post->ID;
                $action = 'updated';
            } else {
                // 3. 创建新文章
                $post_id = $this->create_tool_post($tool_data);
                if (is_wp_error($post_id)) {
                    return array(
                        'success' => false,
                        'message' => '创建文章失败: ' . $post_id->get_error_message(),
                        'errors' => array('post_creation' => $post_id->get_error_message())
                    );
                }
                $action = 'created';
            }
            
            // 4. 上传图片
            $media_ids = $this->handle_images($tool_data, $post_id);
            if (!empty($media_ids['errors'])) {
                $errors = array_merge($errors, $media_ids['errors']);
            }
            
            // 5. 更新ACF字段
            $acf_result = $this->update_acf_fields($post_id, $tool_data, $media_ids);
            if (!$acf_result['success']) {
                $errors = array_merge($errors, $acf_result['errors']);
            }
            
            // 6. 设置分类法
            $taxonomy_result = $this->set_taxonomies($post_id, $tool_data);
            if (!$taxonomy_result['success']) {
                $errors = array_merge($errors, $taxonomy_result['errors']);
            }
            
            return array(
                'success' => true,
                'message' => "AI工具 '{$tool_data['product_name']}' {$action}成功",
                'post_id' => $post_id,
                'action' => $action,
                'warnings' => $errors // 非致命错误作为警告
            );
            
        } catch (Exception $e) {
            return array(
                'success' => false,
                'message' => '处理过程中发生错误: ' . $e->getMessage(),
                'errors' => array('exception' => $e->getMessage())
            );
        }
    }
    
    /**
     * 查找现有工具
     */
    private function find_existing_tool($product_name, $product_url = '') {
        $args = array(
            'post_type' => 'ai_tool',
            'post_status' => array('publish', 'draft'),
            'meta_query' => array(),
            'posts_per_page' => 1
        );
        
        // 优先通过URL查找
        if (!empty($product_url)) {
            $args['meta_query'][] = array(
                'key' => 'product_url',
                'value' => $product_url,
                'compare' => '='
            );
        } else {
            // 通过标题查找
            $args['title'] = $product_name;
        }
        
        $query = new WP_Query($args);
        return $query->have_posts() ? $query->posts[0] : null;
    }
    
    /**
     * 创建工具文章
     */
    private function create_tool_post($tool_data) {
        $post_content = '';
        if (!empty($tool_data['short_introduction'])) {
            $post_content = sanitize_textarea_field($tool_data['short_introduction']);
        }
        if (!empty($tool_data['product_story'])) {
            if (!empty($post_content)) {
                $post_content .= "\n\n";
            }
            $post_content .= sanitize_textarea_field($tool_data['product_story']);
        }
        
        $post_data = array(
            'post_title' => sanitize_text_field($tool_data['product_name']),
            'post_content' => $post_content,
            'post_excerpt' => !empty($tool_data['short_introduction']) ? 
                             substr(sanitize_text_field($tool_data['short_introduction']), 0, 200) : '',
            'post_status' => 'publish',
            'post_type' => 'ai_tool',
            'post_author' => get_current_user_id()
        );
        
        return wp_insert_post($post_data, true);
    }
    
    /**
     * 处理图片上传
     */
    private function handle_images($tool_data, $post_id) {
        $result = array(
            'logo_img' => null,
            'overview_img' => null,
            'errors' => array()
        );
        
        // 上传Logo
        if (!empty($tool_data['logo_img_url'])) {
            $logo_id = $this->upload_image_from_url($tool_data['logo_img_url'], $post_id, 'logo');
            if (is_wp_error($logo_id)) {
                $result['errors']['logo'] = $logo_id->get_error_message();
            } else {
                $result['logo_img'] = $logo_id;
            }
        }
        
        // 上传概览图
        if (!empty($tool_data['overview_img_url'])) {
            $overview_id = $this->upload_image_from_url($tool_data['overview_img_url'], $post_id, 'overview');
            if (is_wp_error($overview_id)) {
                $result['errors']['overview'] = $overview_id->get_error_message();
            } else {
                $result['overview_img'] = $overview_id;
            }
        }
        
        return $result;
    }
    
    /**
     * 从URL上传图片
     */
    private function upload_image_from_url($image_url, $post_id, $type = 'image') {
        // 验证URL
        if (!filter_var($image_url, FILTER_VALIDATE_URL)) {
            return new WP_Error('invalid_url', '无效的图片URL');
        }
        
        // 下载图片
        $response = wp_remote_get($image_url, array(
            'timeout' => 30,
            'headers' => array(
                'User-Agent' => 'WordPress AI Tool Importer/1.0'
            )
        ));
        
        if (is_wp_error($response)) {
            return new WP_Error('download_failed', '图片下载失败: ' . $response->get_error_message());
        }
        
        $body = wp_remote_retrieve_body($response);
        $content_type = wp_remote_retrieve_header($response, 'content-type');
        
        // 验证内容类型
        if (strpos($content_type, 'image/') !== 0) {
            return new WP_Error('invalid_image', '下载的文件不是有效的图片');
        }
        
        // 生成文件名
        $filename = basename(parse_url($image_url, PHP_URL_PATH));
        if (empty($filename) || strpos($filename, '.') === false) {
            $ext = $this->get_image_extension($content_type);
            $filename = $type . '_' . time() . '.' . $ext;
        }
        
        // 上传到媒体库
        $upload = wp_upload_bits($filename, null, $body);
        
        if ($upload['error']) {
            return new WP_Error('upload_failed', '图片上传失败: ' . $upload['error']);
        }
        
        // 创建附件
        $attachment = array(
            'post_mime_type' => $content_type,
            'post_title' => pathinfo($filename, PATHINFO_FILENAME),
            'post_content' => '',
            'post_status' => 'inherit',
            'post_parent' => $post_id
        );
        
        $attach_id = wp_insert_attachment($attachment, $upload['file'], $post_id);
        
        if (is_wp_error($attach_id)) {
            return $attach_id;
        }
        
        // 生成缩略图
        require_once(ABSPATH . 'wp-admin/includes/image.php');
        $attach_data = wp_generate_attachment_metadata($attach_id, $upload['file']);
        wp_update_attachment_metadata($attach_id, $attach_data);
        
        return $attach_id;
    }
    
    /**
     * 根据MIME类型获取文件扩展名
     */
    private function get_image_extension($mime_type) {
        $extensions = array(
            'image/jpeg' => 'jpg',
            'image/png' => 'png',
            'image/gif' => 'gif',
            'image/webp' => 'webp'
        );
        
        return $extensions[$mime_type] ?? 'jpg';
    }
    
    /**
     * 更新ACF字段
     */
    private function update_acf_fields($post_id, $tool_data, $media_ids) {
        $errors = array();
        
        try {
            // 基本字段
            $fields = array(
                'product_url' => $tool_data['product_url'] ?? '',
                'product_story' => $tool_data['product_story'] ?? '',
                'primary_task' => $tool_data['primary_task'] ?? '',
                'author_company' => $tool_data['author_company'] ?? '',
                'general_price_tag' => $tool_data['general_price_tag'] ?? '',
                'initial_release_date' => $tool_data['initial_release_date'] ?? '',
                'is_verified_tool' => $tool_data['is_verified_tool'] ?? false,
                'logo_img' => $media_ids['logo_img'],
                'overview_img' => $media_ids['overview_img']
            );
            
            // 数值字段
            if (isset($tool_data['popularity_score'])) {
                $fields['popularity_score'] = floatval($tool_data['popularity_score']);
            }
            if (isset($tool_data['number_of_tools_by_author'])) {
                $fields['number_of_tools_by_author'] = intval($tool_data['number_of_tools_by_author']);
            }
            if (isset($tool_data['average_rating'])) {
                $fields['average_rating'] = floatval($tool_data['average_rating']);
            }
            if (isset($tool_data['rating_count'])) {
                $fields['rating_count'] = intval($tool_data['rating_count']);
            }
            
            // 价格信息
            if (!empty($tool_data['pricing_details'])) {
                $pricing = $tool_data['pricing_details'];
                $fields['pricing_model'] = $pricing['pricing_model'] ?? '';
                $fields['currency'] = $pricing['currency'] ?? '';
                $fields['billing_frequency'] = $pricing['billing_frequency'] ?? '';
                if (isset($pricing['paid_options_from'])) {
                    $fields['paid_options_from'] = floatval($pricing['paid_options_from']);
                }
            }
            
            // Repeater字段
            $repeater_fields = array(
                'inputs' => 'input_type',
                'outputs' => 'output_type',
                'pros_list' => 'pro_item',
                'cons_list' => 'con_item',
                'related_tasks' => 'task_item'
            );
            
            foreach ($repeater_fields as $field_name => $sub_field) {
                if (!empty($tool_data[$field_name]) && is_array($tool_data[$field_name])) {
                    $repeater_data = array();
                    foreach ($tool_data[$field_name] as $item) {
                        if (is_string($item)) {
                            $repeater_data[] = array($sub_field => $item);
                        } elseif (is_array($item) && isset($item[$sub_field])) {
                            $repeater_data[] = array($sub_field => $item[$sub_field]);
                        }
                    }
                    $fields[$field_name] = $repeater_data;
                }
            }
            
            // 复杂Repeater字段
            if (!empty($tool_data['releases']) && is_array($tool_data['releases'])) {
                $releases = array();
                foreach ($tool_data['releases'] as $release) {
                    if (is_array($release)) {
                        $releases[] = array(
                            'release_date' => $release['release_date'] ?? '',
                            'release_notes' => $release['release_notes'] ?? '',
                            'release_author' => $release['release_author'] ?? ''
                        );
                    }
                }
                $fields['releases'] = $releases;
            }
            
            if (!empty($tool_data['job_impacts']) && is_array($tool_data['job_impacts'])) {
                $job_impacts = array();
                foreach ($tool_data['job_impacts'] as $job) {
                    if (is_array($job)) {
                        $job_impacts[] = array(
                            'job_type' => $job['job_type'] ?? '',
                            'impact_description' => $job['impact_description'] ?? '',
                            'tasks_affected' => $job['tasks_affected'] ?? '',
                            'ai_skills_required' => $job['ai_skills_required'] ?? ''
                        );
                    }
                }
                $fields['job_impacts'] = $job_impacts;
            }
            
            // 更新所有字段
            foreach ($fields as $field_name => $value) {
                if ($value !== null && $value !== '') {
                    $result = update_field($field_name, $value, $post_id);
                    if (!$result) {
                        $errors[] = "更新字段 {$field_name} 失败";
                    }
                }
            }
            
            return array(
                'success' => empty($errors),
                'errors' => $errors
            );
            
        } catch (Exception $e) {
            return array(
                'success' => false,
                'errors' => array('acf_update' => $e->getMessage())
            );
        }
    }
    
    /**
     * 设置分类法
     */
    private function set_taxonomies($post_id, $tool_data) {
        $errors = array();
        
        try {
            // 设置主要分类
            $primary_task = $tool_data['primary_task'] ?? $tool_data['original_category_name'] ?? '';
            if (!empty($primary_task)) {
                $term = get_term_by('name', $primary_task, 'ai_tool_category');
                if (!$term) {
                    $term_result = wp_insert_term($primary_task, 'ai_tool_category');
                    if (is_wp_error($term_result)) {
                        $errors[] = '创建分类失败: ' . $term_result->get_error_message();
                    } else {
                        wp_set_object_terms($post_id, array($term_result['term_id']), 'ai_tool_category');
                    }
                } else {
                    wp_set_object_terms($post_id, array($term->term_id), 'ai_tool_category');
                }
            }
            
            return array(
                'success' => empty($errors),
                'errors' => $errors
            );
            
        } catch (Exception $e) {
            return array(
                'success' => false,
                'errors' => array('taxonomy' => $e->getMessage())
            );
        }
    }
}

// 初始化插件
new AIToolImportAPI();

/**
 * 激活插件时的处理
 */
register_activation_hook(__FILE__, function() {
    // 刷新重写规则
    flush_rewrite_rules();
});

/**
 * 停用插件时的处理
 */
register_deactivation_hook(__FILE__, function() {
    // 清理重写规则
    flush_rewrite_rules();
}); 