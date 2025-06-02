<?php
/**
 * Plugin Name: AI工具导入API
 * Description: 自定义API端点用于批量导入AI工具数据到aihub CPT
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
            'post_type' => 'aihub',  // 修改为aihub CPT
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
            'post_type' => 'aihub',  // 修改为aihub CPT
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
        
        // 上传Logo - 优先使用提供的logo_img_url，否则尝试获取favicon
        $logo_url = null;
        if (!empty($tool_data['logo_img_url'])) {
            $logo_url = $tool_data['logo_img_url'];
        } elseif (!empty($tool_data['product_url'])) {
            // 尝试从product_url获取favicon
            $logo_url = $this->get_favicon_url($tool_data['product_url']);
            if ($logo_url) {
                error_log("AI Tool Import: 从favicon获取logo: " . $logo_url);
            }
        }
        
        if ($logo_url) {
            $logo_id = $this->upload_image_from_url($logo_url, $post_id, 'logo');
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
            // 1. 基本信息 (AI Tool Basic Info)
            $basic_fields = array(
                'product_url' => $tool_data['product_url'] ?? '',
                'logo_img' => $media_ids['logo_img'],
                'overview_img' => $media_ids['overview_img'],
                'product_story' => $tool_data['product_story'] ?? '',
                'author_company' => $tool_data['author_company'] ?? '',
                'general_price_tag' => $tool_data['general_price_tag'] ?? '',
                'initial_release_date' => $tool_data['initial_release_date'] ?? '',
                'message' => $tool_data['message'] ?? '',
                'is_verified_tool' => $tool_data['is_verified_tool'] ?? false,
                'copy_url_text' => $tool_data['copy_url_text'] ?? 'Copy URL',
                'save_button_text' => $tool_data['save_button_text'] ?? 'Save',
                'vote_best_ai_tool_text' => $tool_data['vote_best_ai_tool_text'] ?? 'Vote Best AI Tool'
            );
            
            // 数值字段
            if (isset($tool_data['popularity_score'])) {
                $basic_fields['popularity_score'] = floatval($tool_data['popularity_score']);
            }
            if (isset($tool_data['number_of_tools_by_author'])) {
                $basic_fields['number_of_tools_by_author'] = intval($tool_data['number_of_tools_by_author']);
            }
            
            // 2. 输入输出 (AI Tool IO)
            if (!empty($tool_data['inputs']) && is_array($tool_data['inputs'])) {
                $inputs_data = array();
                foreach ($tool_data['inputs'] as $input) {
                    if (is_string($input)) {
                        $inputs_data[] = array('input_type' => $input);
                    } elseif (is_array($input) && isset($input['input_type'])) {
                        $inputs_data[] = array('input_type' => $input['input_type']);
                    }
                }
                $basic_fields['inputs'] = $inputs_data;
            }
            
            if (!empty($tool_data['outputs']) && is_array($tool_data['outputs'])) {
                $outputs_data = array();
                foreach ($tool_data['outputs'] as $output) {
                    if (is_string($output)) {
                        $outputs_data[] = array('output_type' => $output);
                    } elseif (is_array($output) && isset($output['output_type'])) {
                        $outputs_data[] = array('output_type' => $output['output_type']);
                    }
                }
                $basic_fields['outputs'] = $outputs_data;
            }
            
            // 3. 定价 (AI Tool Pricing)
            if (!empty($tool_data['pricing_details'])) {
                $pricing = $tool_data['pricing_details'];
                $basic_fields['pricing_model'] = $pricing['pricing_model'] ?? '';
                $basic_fields['currency'] = $pricing['currency'] ?? '';
                $basic_fields['billing_frequency'] = $pricing['billing_frequency'] ?? '';
                if (isset($pricing['paid_options_from'])) {
                    $basic_fields['paid_options_from'] = floatval($pricing['paid_options_from']);
                }
            }
            
            // 4. 版本发布 (AI Tool Releases)
            if (!empty($tool_data['releases']) && is_array($tool_data['releases'])) {
                $releases_data = array();
                foreach ($tool_data['releases'] as $release) {
                    if (is_array($release)) {
                        $releases_data[] = array(
                            'release_product_name' => $release['release_product_name'] ?? $release['product_name'] ?? '',
                            'release_date' => $release['release_date'] ?? '',
                            'release_notes' => $release['release_notes'] ?? '',
                            'release_author' => $release['release_author'] ?? $release['author'] ?? ''
                        );
                    }
                }
                $basic_fields['releases'] = $releases_data;
            }
            
            // 5. 评论/评分 (AI Tool Reviews)
            if (isset($tool_data['user_ratings_count'])) {
                $basic_fields['user_ratings_count'] = intval($tool_data['user_ratings_count']);
            }
            if (isset($tool_data['average_rating'])) {
                $basic_fields['average_rating'] = floatval($tool_data['average_rating']);
            }
            $basic_fields['how_would_you_rate_text'] = $tool_data['how_would_you_rate_text'] ?? 'How would you rate this tool?';
            $basic_fields['help_other_people_text'] = $tool_data['help_other_people_text'] ?? 'Help other people by letting them know what you think.';
            $basic_fields['your_rating_text'] = $tool_data['your_rating_text'] ?? 'Your rating';
            $basic_fields['post_review_button_text'] = $tool_data['post_review_button_text'] ?? 'Post Review';
            $basic_fields['feature_requests_intro'] = $tool_data['feature_requests_intro'] ?? 'Feature requests';
            $basic_fields['request_feature_button_text'] = $tool_data['request_feature_button_text'] ?? 'Request a feature';
            
            // 6. 工作影响 (AI Tool Job Impacts)
            if (!empty($tool_data['job_impacts']) && is_array($tool_data['job_impacts'])) {
                $job_impacts_data = array();
                foreach ($tool_data['job_impacts'] as $job) {
                    if (is_array($job)) {
                        $job_impacts_data[] = array(
                            'job_type' => $job['job_type'] ?? '',
                            'impact_description' => $job['impact_description'] ?? '',
                            'tasks_affected' => $job['tasks_affected'] ?? '',
                            'ai_skills_required' => $job['ai_skills_required'] ?? ''
                        );
                    }
                }
                $basic_fields['job_impacts'] = $job_impacts_data;
            }
            
            // 7. 优缺点 (AI Tool Pros & Cons)
            if (!empty($tool_data['pros_list']) && is_array($tool_data['pros_list'])) {
                $pros_data = array();
                foreach ($tool_data['pros_list'] as $pro) {
                    if (is_string($pro)) {
                        $pros_data[] = array('pro_item' => $pro);
                    } elseif (is_array($pro) && isset($pro['pro_item'])) {
                        $pros_data[] = array('pro_item' => $pro['pro_item']);
                    }
                }
                $basic_fields['pros_list'] = $pros_data;
            }
            
            if (!empty($tool_data['cons_list']) && is_array($tool_data['cons_list'])) {
                $cons_data = array();
                foreach ($tool_data['cons_list'] as $con) {
                    if (is_string($con)) {
                        $cons_data[] = array('con_item' => $con);
                    } elseif (is_array($con) && isset($con['con_item'])) {
                        $cons_data[] = array('con_item' => $con['con_item']);
                    }
                }
                $basic_fields['cons_list'] = $cons_data;
            }
            
            $basic_fields['view_more_pros_text'] = $tool_data['view_more_pros_text'] ?? 'View more pros';
            $basic_fields['view_more_cons_text'] = $tool_data['view_more_cons_text'] ?? 'View more cons';
            
            if (!empty($tool_data['related_tasks']) && is_array($tool_data['related_tasks'])) {
                $tasks_data = array();
                foreach ($tool_data['related_tasks'] as $task) {
                    if (is_string($task)) {
                        $tasks_data[] = array('task_item' => $task);
                    } elseif (is_array($task) && isset($task['task_item'])) {
                        $tasks_data[] = array('task_item' => $task['task_item']);
                    }
                }
                $basic_fields['related_tasks'] = $tasks_data;
            }
            
            // 8. 替代方案 (AI Tool Alternatives)
            $basic_fields['alternatives_count_text'] = $tool_data['alternatives_count_text'] ?? 'Alternatives to this tool';
            $basic_fields['view_more_alternatives_text'] = $tool_data['view_more_alternatives_text'] ?? 'View more alternatives';
            
            if (!empty($tool_data['alternatives']) && is_array($tool_data['alternatives'])) {
                $alternatives_data = array();
                foreach ($tool_data['alternatives'] as $alt) {
                    if (is_array($alt)) {
                        $alternatives_data[] = array(
                            'alternative_tool_name' => $alt['alternative_tool_name'] ?? $alt['name'] ?? '',
                            'alternative_tool_url' => $alt['alternative_tool_url'] ?? $alt['url'] ?? '',
                            'relationship_type' => $alt['relationship_type'] ?? 'Alternative'
                        );
                    }
                }
                $basic_fields['alternatives'] = $alternatives_data;
            }
            
            // 9. 推荐工具 (AI Tool See Also)
            $basic_fields['if_you_liked_text'] = $tool_data['if_you_liked_text'] ?? 'If you liked this tool, you might also like';
            
            if (!empty($tool_data['featured_matches']) && is_array($tool_data['featured_matches'])) {
                $featured_data = array();
                foreach ($tool_data['featured_matches'] as $match) {
                    if (is_array($match)) {
                        $featured_data[] = array(
                            'matched_tool_name' => $match['matched_tool_name'] ?? $match['name'] ?? '',
                            'matched_tool_url' => $match['matched_tool_url'] ?? $match['url'] ?? ''
                        );
                    }
                }
                $basic_fields['featured_matches'] = $featured_data;
            }
            
            if (!empty($tool_data['other_tools']) && is_array($tool_data['other_tools'])) {
                $other_tools_data = array();
                foreach ($tool_data['other_tools'] as $tool) {
                    if (is_array($tool)) {
                        $other_tools_data[] = array(
                            'other_tool_item_name' => $tool['other_tool_item_name'] ?? $tool['name'] ?? '',
                            'other_tool_item_url' => $tool['other_tool_item_url'] ?? $tool['url'] ?? ''
                        );
                    }
                }
                $basic_fields['other_tools'] = $other_tools_data;
            }
            
            // 更新所有字段
            foreach ($basic_fields as $field_name => $value) {
                if ($value !== null && $value !== '') {
                    $result = update_field($field_name, $value, $post_id);
                    if (!$result && $value !== false && $value !== 0) {
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
            // 1. 设置主要分类 (aihub_category)
            $primary_category = $tool_data['category'] ?? $tool_data['original_category_name'] ?? $tool_data['primary_task'] ?? '';
            if (!empty($primary_category)) {
                $category_result = $this->create_or_get_term($primary_category, 'aihub_category');
                if ($category_result['success']) {
                    wp_set_object_terms($post_id, array($category_result['term_id']), 'aihub_category');
                } else {
                    $errors[] = $category_result['error'];
                }
            }
            
            // 2. 设置AI标签 (aihub_ai_tags)
            $ai_tags = array();
            
            // 从各种字段收集标签
            if (!empty($tool_data['primary_task'])) {
                $ai_tags[] = $tool_data['primary_task'];
            }
            if (!empty($tool_data['inputs']) && is_array($tool_data['inputs'])) {
                $ai_tags = array_merge($ai_tags, $tool_data['inputs']);
            }
            if (!empty($tool_data['outputs']) && is_array($tool_data['outputs'])) {
                $ai_tags = array_merge($ai_tags, $tool_data['outputs']);
            }
            if (!empty($tool_data['general_price_tag'])) {
                $ai_tags[] = $tool_data['general_price_tag'];
            }
            
            // 从category生成标签
            if (!empty($primary_category)) {
                $ai_tags[] = $primary_category;
            }
            
            // 创建AI标签
            $tag_ids = array();
            foreach (array_unique($ai_tags) as $tag_name) {
                if (!empty(trim($tag_name))) {
                    $tag_result = $this->create_or_get_term(trim($tag_name), 'aihub_ai_tags');
                    if ($tag_result['success']) {
                        $tag_ids[] = $tag_result['term_id'];
                    } else {
                        $errors[] = $tag_result['error'];
                    }
                }
            }
            
            if (!empty($tag_ids)) {
                wp_set_object_terms($post_id, $tag_ids, 'aihub_ai_tags');
            }
            
            // 3. 设置定价模式 (aihub_pricing)
            $pricing_model = $tool_data['general_price_tag'] ?? 
                           ($tool_data['pricing_details']['pricing_model'] ?? '');
            
            if (!empty($pricing_model)) {
                $pricing_result = $this->create_or_get_term($pricing_model, 'aihub_pricing');
                if ($pricing_result['success']) {
                    wp_set_object_terms($post_id, array($pricing_result['term_id']), 'aihub_pricing');
                } else {
                    $errors[] = $pricing_result['error'];
                }
            }
            
            // 4. 设置输入类型 (aihub_input_types)
            if (!empty($tool_data['inputs']) && is_array($tool_data['inputs'])) {
                $input_ids = array();
                foreach ($tool_data['inputs'] as $input_type) {
                    if (!empty(trim($input_type))) {
                        $input_result = $this->create_or_get_term(trim($input_type), 'aihub_input_types');
                        if ($input_result['success']) {
                            $input_ids[] = $input_result['term_id'];
                        } else {
                            $errors[] = $input_result['error'];
                        }
                    }
                }
                if (!empty($input_ids)) {
                    wp_set_object_terms($post_id, $input_ids, 'aihub_input_types');
                }
            }
            
            // 5. 设置输出类型 (aihub_output_types)
            if (!empty($tool_data['outputs']) && is_array($tool_data['outputs'])) {
                $output_ids = array();
                foreach ($tool_data['outputs'] as $output_type) {
                    if (!empty(trim($output_type))) {
                        $output_result = $this->create_or_get_term(trim($output_type), 'aihub_output_types');
                        if ($output_result['success']) {
                            $output_ids[] = $output_result['term_id'];
                        } else {
                            $errors[] = $output_result['error'];
                        }
                    }
                }
                if (!empty($output_ids)) {
                    wp_set_object_terms($post_id, $output_ids, 'aihub_output_types');
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
    
    /**
     * 创建或获取分类法术语
     */
    private function create_or_get_term($term_name, $taxonomy) {
        try {
            // 清理术语名称
            $term_name = trim($term_name);
            if (empty($term_name)) {
                return array(
                    'success' => false,
                    'error' => "术语名称不能为空 (taxonomy: {$taxonomy})"
                );
            }
            
            // 检查术语是否已存在
            $existing_term = get_term_by('name', $term_name, $taxonomy);
            if ($existing_term && !is_wp_error($existing_term)) {
                return array(
                    'success' => true,
                    'term_id' => $existing_term->term_id,
                    'action' => 'found'
                );
            }
            
            // 也尝试按slug查找
            $slug = sanitize_title($term_name);
            $existing_term = get_term_by('slug', $slug, $taxonomy);
            if ($existing_term && !is_wp_error($existing_term)) {
                return array(
                    'success' => true,
                    'term_id' => $existing_term->term_id,
                    'action' => 'found_by_slug'
                );
            }
            
            // 创建新术语
            $term_result = wp_insert_term($term_name, $taxonomy, array(
                'slug' => $slug
            ));
            
            if (is_wp_error($term_result)) {
                // 检查是否是重复术语错误
                if ($term_result->get_error_code() === 'term_exists') {
                    $term_id = $term_result->get_error_data();
                    return array(
                        'success' => true,
                        'term_id' => $term_id,
                        'action' => 'existed'
                    );
                }
                
                return array(
                    'success' => false,
                    'error' => "创建术语失败 ({$taxonomy}: {$term_name}): " . $term_result->get_error_message()
                );
            }
            
            return array(
                'success' => true,
                'term_id' => $term_result['term_id'],
                'action' => 'created'
            );
            
        } catch (Exception $e) {
            return array(
                'success' => false,
                'error' => "处理术语异常 ({$taxonomy}: {$term_name}): " . $e->getMessage()
            );
        }
    }
    
    /**
     * 从网站URL获取favicon
     */
    private function get_favicon_url($website_url, $timeout = 10) {
        if (empty($website_url)) {
            return null;
        }
        
        try {
            // 标准化URL
            if (!preg_match('/^https?:\/\//', $website_url)) {
                $website_url = 'https://' . $website_url;
            }
            
            $parsed_url = parse_url($website_url);
            if (!$parsed_url || empty($parsed_url['host'])) {
                return null;
            }
            
            $base_url = $parsed_url['scheme'] . '://' . $parsed_url['host'];
            
            // 方法1: 尝试标准favicon路径
            $standard_favicon = $base_url . '/favicon.ico';
            if ($this->check_url_exists($standard_favicon, $timeout)) {
                return $standard_favicon;
            }
            
            // 方法2: 解析HTML中的favicon链接
            $response = wp_remote_get($website_url, array(
                'timeout' => $timeout,
                'headers' => array(
                    'User-Agent' => 'WordPress AI Tool Importer/1.0'
                )
            ));
            
            if (!is_wp_error($response) && wp_remote_retrieve_response_code($response) === 200) {
                $html = wp_remote_retrieve_body($response);
                $favicon_url = $this->parse_favicon_from_html($html, $base_url);
                if ($favicon_url && $this->check_url_exists($favicon_url, $timeout)) {
                    return $favicon_url;
                }
            }
            
            // 方法3: 尝试常见的favicon路径
            $common_paths = array(
                '/favicon.png',
                '/favicon.svg',
                '/apple-touch-icon.png',
                '/apple-touch-icon-180x180.png',
                '/android-chrome-192x192.png',
                '/logo.png',
                '/logo.svg'
            );
            
            foreach ($common_paths as $path) {
                $favicon_url = $base_url . $path;
                if ($this->check_url_exists($favicon_url, $timeout)) {
                    return $favicon_url;
                }
            }
            
            // 方法4: 使用第三方favicon服务
            $fallback_services = array(
                "https://www.google.com/s2/favicons?domain={$parsed_url['host']}&sz=64",
                "https://favicon.yandex.net/favicon/{$parsed_url['host']}",
                "https://icons.duckduckgo.com/ip3/{$parsed_url['host']}.ico"
            );
            
            foreach ($fallback_services as $service_url) {
                if ($this->check_url_exists($service_url, $timeout)) {
                    return $service_url;
                }
            }
            
            return null;
            
        } catch (Exception $e) {
            error_log("AI Tool Import: 获取favicon失败: " . $e->getMessage());
            return null;
        }
    }
    
    /**
     * 检查URL是否存在且返回图片
     */
    private function check_url_exists($url, $timeout = 5) {
        $response = wp_remote_head($url, array(
            'timeout' => $timeout,
            'headers' => array(
                'User-Agent' => 'WordPress AI Tool Importer/1.0'
            )
        ));
        
        if (is_wp_error($response)) {
            return false;
        }
        
        $status_code = wp_remote_retrieve_response_code($response);
        if ($status_code !== 200) {
            return false;
        }
        
        // 检查内容类型
        $content_type = wp_remote_retrieve_header($response, 'content-type');
        if (empty($content_type)) {
            return true; // 如果没有内容类型，假设是有效的
        }
        
        return strpos($content_type, 'image/') === 0 || strpos($content_type, 'application/octet-stream') === 0;
    }
    
    /**
     * 从HTML中解析favicon链接
     */
    private function parse_favicon_from_html($html, $base_url) {
        // 查找各种favicon相关的link标签
        $patterns = array(
            '/<link[^>]*rel=["\'](?:shortcut )?icon["\'][^>]*href=["\']([^"\']+)["\']/i',
            '/<link[^>]*href=["\']([^"\']+)["\'][^>]*rel=["\'](?:shortcut )?icon["\']/i',
            '/<link[^>]*rel=["\']apple-touch-icon["\'][^>]*href=["\']([^"\']+)["\']/i',
            '/<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']/i'
        );
        
        foreach ($patterns as $pattern) {
            if (preg_match_all($pattern, $html, $matches)) {
                foreach ($matches[1] as $match) {
                    // 转换为绝对URL
                    if (strpos($match, 'http') === 0) {
                        $favicon_url = $match;
                    } else {
                        $favicon_url = rtrim($base_url, '/') . '/' . ltrim($match, '/');
                    }
                    
                    // 验证URL是否有效
                    if ($this->check_url_exists($favicon_url)) {
                        return $favicon_url;
                    }
                }
            }
        }
        
        return null;
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