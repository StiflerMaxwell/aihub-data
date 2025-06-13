<?php
/**
 * ACF字段组自动配置脚本
 * 为aihub文章类型创建完整的ACF字段组
 */

// WordPress环境
define('WP_USE_THEMES', false);
require_once('wp-config.php');

if (!function_exists('acf_add_local_field_group')) {
    die("Error: ACF插件未安装或未激活！\n");
}

echo "🚀 开始创建ACF字段组...\n\n";

// 基础信息字段组
acf_add_local_field_group(array(
    'key' => 'group_aihub_basic_info',
    'title' => 'AI工具 - 基础信息',
    'fields' => array(
        array(
            'key' => 'field_product_name',
            'label' => '产品名称',
            'name' => 'product_name',
            'type' => 'text',
            'required' => 1,
        ),
        array(
            'key' => 'field_product_url',
            'label' => '产品URL',
            'name' => 'product_url',
            'type' => 'url',
        ),
        array(
            'key' => 'field_short_introduction',
            'label' => '简短介绍',
            'name' => 'short_introduction',
            'type' => 'textarea',
        ),
        array(
            'key' => 'field_product_story',
            'label' => '产品故事',
            'name' => 'product_story',
            'type' => 'wysiwyg',
        ),
        array(
            'key' => 'field_author_company',
            'label' => '开发公司',
            'name' => 'author_company',
            'type' => 'text',
        ),
        array(
            'key' => 'field_primary_task',
            'label' => '主要任务',
            'name' => 'primary_task',
            'type' => 'text',
        ),
        array(
            'key' => 'field_category',
            'label' => '分类',
            'name' => 'category',
            'type' => 'text',
        ),
        array(
            'key' => 'field_original_category_name',
            'label' => '原始分类名',
            'name' => 'original_category_name',
            'type' => 'text',
        ),
    ),
    'location' => array(
        array(
            array(
                'param' => 'post_type',
                'operator' => '==',
                'value' => 'aihub',
            ),
        ),
    ),
));

// 媒体资源字段组
acf_add_local_field_group(array(
    'key' => 'group_aihub_media',
    'title' => 'AI工具 - 媒体资源',
    'fields' => array(
        array(
            'key' => 'field_logo_img_url',
            'label' => 'Logo图片URL',
            'name' => 'logo_img_url',
            'type' => 'url',
        ),
        array(
            'key' => 'field_overview_img_url',
            'label' => '概览图片URL',
            'name' => 'overview_img_url',
            'type' => 'url',
        ),
        array(
            'key' => 'field_demo_video_url',
            'label' => '演示视频URL',
            'name' => 'demo_video_url',
            'type' => 'url',
        ),
    ),
    'location' => array(
        array(
            array(
                'param' => 'post_type',
                'operator' => '==',
                'value' => 'aihub',
            ),
        ),
    ),
));

// 数值字段组
acf_add_local_field_group(array(
    'key' => 'group_aihub_numbers',
    'title' => 'AI工具 - 数值信息',
    'fields' => array(
        array(
            'key' => 'field_average_rating',
            'label' => '平均评分',
            'name' => 'average_rating',
            'type' => 'number',
            'min' => 0,
            'max' => 5,
            'step' => 0.1,
        ),
        array(
            'key' => 'field_popularity_score',
            'label' => '热度评分',
            'name' => 'popularity_score',
            'type' => 'number',
            'min' => 0,
        ),
        array(
            'key' => 'field_user_ratings_count',
            'label' => '用户评分数量',
            'name' => 'user_ratings_count',
            'type' => 'number',
            'min' => 0,
        ),
        array(
            'key' => 'field_number_of_tools_by_author',
            'label' => '作者工具数量',
            'name' => 'number_of_tools_by_author',
            'type' => 'number',
            'min' => 0,
        ),
        array(
            'key' => 'field_is_verified_tool',
            'label' => '是否已验证',
            'name' => 'is_verified_tool',
            'type' => 'true_false',
            'default_value' => 0,
        ),
    ),
    'location' => array(
        array(
            array(
                'param' => 'post_type',
                'operator' => '==',
                'value' => 'aihub',
            ),
        ),
    ),
));

// 定价信息字段组
acf_add_local_field_group(array(
    'key' => 'group_aihub_pricing',
    'title' => 'AI工具 - 定价信息',
    'fields' => array(
        array(
            'key' => 'field_general_price_tag',
            'label' => '定价标签',
            'name' => 'general_price_tag',
            'type' => 'text',
        ),
        array(
            'key' => 'field_initial_release_date',
            'label' => '初始发布日期',
            'name' => 'initial_release_date',
            'type' => 'text',
        ),
        array(
            'key' => 'field_pricing_details',
            'label' => '详细定价信息',
            'name' => 'pricing_details',
            'type' => 'textarea',
            'instructions' => 'JSON格式的定价详情',
        ),
    ),
    'location' => array(
        array(
            array(
                'param' => 'post_type',
                'operator' => '==',
                'value' => 'aihub',
            ),
        ),
    ),
));

// UI文本字段组
acf_add_local_field_group(array(
    'key' => 'group_aihub_ui_text',
    'title' => 'AI工具 - UI文本',
    'fields' => array(
        array(
            'key' => 'field_message',
            'label' => '消息文本',
            'name' => 'message',
            'type' => 'text',
        ),
        array(
            'key' => 'field_copy_url_text',
            'label' => '复制URL文本',
            'name' => 'copy_url_text',
            'type' => 'text',
        ),
        array(
            'key' => 'field_save_button_text',
            'label' => '保存按钮文本',
            'name' => 'save_button_text',
            'type' => 'text',
        ),
        array(
            'key' => 'field_vote_best_ai_tool_text',
            'label' => '投票文本',
            'name' => 'vote_best_ai_tool_text',
            'type' => 'text',
        ),
        array(
            'key' => 'field_how_would_you_rate_text',
            'label' => '评分询问文本',
            'name' => 'how_would_you_rate_text',
            'type' => 'text',
        ),
        array(
            'key' => 'field_help_other_people_text',
            'label' => '帮助他人文本',
            'name' => 'help_other_people_text',
            'type' => 'text',
        ),
        array(
            'key' => 'field_your_rating_text',
            'label' => '您的评分文本',
            'name' => 'your_rating_text',
            'type' => 'text',
        ),
        array(
            'key' => 'field_post_review_button_text',
            'label' => '发布评论按钮文本',
            'name' => 'post_review_button_text',
            'type' => 'text',
        ),
        array(
            'key' => 'field_feature_requests_intro',
            'label' => '功能请求介绍',
            'name' => 'feature_requests_intro',
            'type' => 'text',
        ),
        array(
            'key' => 'field_request_feature_button_text',
            'label' => '请求功能按钮文本',
            'name' => 'request_feature_button_text',
            'type' => 'text',
        ),
        array(
            'key' => 'field_view_more_pros_text',
            'label' => '查看更多优点文本',
            'name' => 'view_more_pros_text',
            'type' => 'text',
        ),
        array(
            'key' => 'field_view_more_cons_text',
            'label' => '查看更多缺点文本',
            'name' => 'view_more_cons_text',
            'type' => 'text',
        ),
        array(
            'key' => 'field_alternatives_count_text',
            'label' => '替代工具数量文本',
            'name' => 'alternatives_count_text',
            'type' => 'text',
        ),
        array(
            'key' => 'field_view_more_alternatives_text',
            'label' => '查看更多替代工具文本',
            'name' => 'view_more_alternatives_text',
            'type' => 'text',
        ),
        array(
            'key' => 'field_if_you_liked_text',
            'label' => '推荐文本',
            'name' => 'if_you_liked_text',
            'type' => 'text',
        ),
    ),
    'location' => array(
        array(
            array(
                'param' => 'post_type',
                'operator' => '==',
                'value' => 'aihub',
            ),
        ),
    ),
));

// 数组字段组
acf_add_local_field_group(array(
    'key' => 'group_aihub_arrays',
    'title' => 'AI工具 - 数组字段',
    'fields' => array(
        array(
            'key' => 'field_inputs',
            'label' => '输入类型',
            'name' => 'inputs',
            'type' => 'textarea',
            'instructions' => 'JSON数组格式',
        ),
        array(
            'key' => 'field_outputs',
            'label' => '输出类型',
            'name' => 'outputs',
            'type' => 'textarea',
            'instructions' => 'JSON数组格式',
        ),
        array(
            'key' => 'field_features',
            'label' => '功能特性',
            'name' => 'features',
            'type' => 'textarea',
            'instructions' => 'JSON数组格式',
        ),
        array(
            'key' => 'field_pros_list',
            'label' => '优点列表',
            'name' => 'pros_list',
            'type' => 'textarea',
            'instructions' => 'JSON数组格式',
        ),
        array(
            'key' => 'field_cons_list',
            'label' => '缺点列表',
            'name' => 'cons_list',
            'type' => 'textarea',
            'instructions' => 'JSON数组格式',
        ),
        array(
            'key' => 'field_related_tasks',
            'label' => '相关任务',
            'name' => 'related_tasks',
            'type' => 'textarea',
            'instructions' => 'JSON数组格式',
        ),
        array(
            'key' => 'field_alternative_tools',
            'label' => '替代工具',
            'name' => 'alternative_tools',
            'type' => 'textarea',
            'instructions' => 'JSON数组格式',
        ),
        array(
            'key' => 'field_featured_matches',
            'label' => '精选匹配',
            'name' => 'featured_matches',
            'type' => 'textarea',
            'instructions' => 'JSON数组格式',
        ),
        array(
            'key' => 'field_other_tools',
            'label' => '其他工具',
            'name' => 'other_tools',
            'type' => 'textarea',
            'instructions' => 'JSON数组格式',
        ),
    ),
    'location' => array(
        array(
            array(
                'param' => 'post_type',
                'operator' => '==',
                'value' => 'aihub',
            ),
        ),
    ),
));

// 复杂对象字段组
acf_add_local_field_group(array(
    'key' => 'group_aihub_complex',
    'title' => 'AI工具 - 复杂对象',
    'fields' => array(
        array(
            'key' => 'field_releases',
            'label' => '版本发布信息',
            'name' => 'releases',
            'type' => 'textarea',
            'instructions' => 'JSON数组格式的版本发布信息',
        ),
        array(
            'key' => 'field_job_impacts',
            'label' => '工作影响分析',
            'name' => 'job_impacts',
            'type' => 'textarea',
            'instructions' => 'JSON数组格式的工作影响信息',
        ),
        array(
            'key' => 'field_alternatives',
            'label' => '替代方案',
            'name' => 'alternatives',
            'type' => 'textarea',
            'instructions' => 'JSON数组格式的替代方案',
        ),
    ),
    'location' => array(
        array(
            array(
                'param' => 'post_type',
                'operator' => '==',
                'value' => 'aihub',
            ),
        ),
    ),
));

echo "✅ ACF字段组创建完成！\n\n";
echo "📋 已创建的字段组:\n";
echo "   • AI工具 - 基础信息 (8个字段)\n";
echo "   • AI工具 - 媒体资源 (3个字段)\n";
echo "   • AI工具 - 数值信息 (5个字段)\n";
echo "   • AI工具 - 定价信息 (3个字段)\n";
echo "   • AI工具 - UI文本 (15个字段)\n";
echo "   • AI工具 - 数组字段 (9个字段)\n";
echo "   • AI工具 - 复杂对象 (3个字段)\n";
echo "📊 总计: 46个ACF字段\n\n";
echo "🎯 下一步: 重新导入数据以验证字段保存\n";
?> 