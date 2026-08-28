-- 打工人人格测试模块（MySQL 8.0+）
-- 依赖既有用户表：wx_mini_user(id BIGINT UNSIGNED)
-- 字符集：utf8mb4；时间字段统一使用服务器时区（建议业务层使用 Asia/Shanghai）。

SET NAMES utf8mb4;

-- 1. 测试产品：当前仅一条 code = worker_personality。
CREATE TABLE IF NOT EXISTS `personality_test` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  `code` VARCHAR(64) NOT NULL COMMENT '测试唯一编码',
  `title` VARCHAR(100) NOT NULL COMMENT '测试标题',
  `description` VARCHAR(255) DEFAULT NULL COMMENT '测试说明',
  `question_count` TINYINT UNSIGNED NOT NULL DEFAULT 8 COMMENT '单次抽题数量',
  `daily_limit` TINYINT UNSIGNED NOT NULL DEFAULT 3 COMMENT '单用户每日完成上限，0 表示不限制',
  `status` TINYINT UNSIGNED NOT NULL DEFAULT 1 COMMENT '状态：0停用，1启用',
  `current_version_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '当前已发布版本 ID（发布后回填；避免版本表循环外键，业务层校验）',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_personality_test_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='人格测试定义';

-- 2. 测试版本：题库、计分逻辑和结果模板均以版本发布，历史报告不受后续改题影响。
CREATE TABLE IF NOT EXISTS `personality_test_version` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  `test_id` BIGINT UNSIGNED NOT NULL COMMENT 'personality_test.id',
  `version_no` VARCHAR(32) NOT NULL COMMENT '版本号，例如 v1.0.0',
  `algorithm_version` VARCHAR(32) NOT NULL DEFAULT 'v1' COMMENT '计分算法版本',
  `status` TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '状态：0草稿，1已发布，2已归档',
  `published_at` DATETIME DEFAULT NULL COMMENT '发布时间',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_personality_test_version` (`test_id`, `version_no`),
  KEY `idx_personality_test_version_status` (`test_id`, `status`),
  CONSTRAINT `fk_personality_test_version_test`
    FOREIGN KEY (`test_id`) REFERENCES `personality_test` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='人格测试版本';

-- 3. 计分维度：首发可初始化 DRIVE / BOUNDARY / ENERGY / CREATIVE。
CREATE TABLE IF NOT EXISTS `personality_dimension` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  `code` VARCHAR(32) NOT NULL COMMENT '维度编码',
  `name` VARCHAR(50) NOT NULL COMMENT '维度名称',
  `description` VARCHAR(255) DEFAULT NULL COMMENT '维度说明',
  `sort` SMALLINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '展示排序',
  `status` TINYINT UNSIGNED NOT NULL DEFAULT 1 COMMENT '状态：0停用，1启用',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_personality_dimension_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='人格计分维度';

-- 4. 题目。已发布版本中的内容不直接修改；修改时复制出新版本。
CREATE TABLE IF NOT EXISTS `personality_question` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  `version_id` BIGINT UNSIGNED NOT NULL COMMENT 'personality_test_version.id',
  `code` VARCHAR(32) NOT NULL COMMENT '题目编码，例如 Q01',
  `stem` VARCHAR(500) NOT NULL COMMENT '题干',
  `sort` SMALLINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '排序/抽题权重排序',
  `status` TINYINT UNSIGNED NOT NULL DEFAULT 1 COMMENT '状态：0下线，1启用',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_personality_question_version_code` (`version_id`, `code`),
  KEY `idx_personality_question_pick` (`version_id`, `status`, `sort`),
  CONSTRAINT `fk_personality_question_version`
    FOREIGN KEY (`version_id`) REFERENCES `personality_test_version` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='人格测试题目';

-- 5. 选项。每一题通常四个选项；score 仅存服务端，接口不可下发。
CREATE TABLE IF NOT EXISTS `personality_option` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  `question_id` BIGINT UNSIGNED NOT NULL COMMENT 'personality_question.id',
  `code` CHAR(1) NOT NULL COMMENT '选项编码 A-D',
  `content` VARCHAR(500) NOT NULL COMMENT '选项文案',
  `dimension_id` BIGINT UNSIGNED NOT NULL COMMENT 'personality_dimension.id',
  `score` TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '该选项对应维度得分，0-10',
  `sort` SMALLINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '默认展示排序（实际会话可随机）',
  `status` TINYINT UNSIGNED NOT NULL DEFAULT 1 COMMENT '状态：0下线，1启用',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_personality_option_question_code` (`question_id`, `code`),
  KEY `idx_personality_option_question` (`question_id`, `status`, `sort`),
  CONSTRAINT `fk_personality_option_question`
    FOREIGN KEY (`question_id`) REFERENCES `personality_question` (`id`),
  CONSTRAINT `fk_personality_option_dimension`
    FOREIGN KEY (`dimension_id`) REFERENCES `personality_dimension` (`id`),
  CONSTRAINT `ck_personality_option_score` CHECK (`score` <= 10)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='人格测试题目选项及得分';

-- 6. 结果模板：按版本和主维度配置；报告生成后会完整写入 report_snapshot_json。
CREATE TABLE IF NOT EXISTS `personality_result_profile` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  `version_id` BIGINT UNSIGNED NOT NULL COMMENT 'personality_test_version.id',
  `code` VARCHAR(64) NOT NULL COMMENT '结果编码，例如 BOUNDARY_MASTER',
  `primary_dimension_id` BIGINT UNSIGNED NOT NULL COMMENT '主维度',
  `min_score` DECIMAL(5,2) NOT NULL DEFAULT 0.00 COMMENT '归一化分数下限（含）',
  `max_score` DECIMAL(5,2) NOT NULL DEFAULT 100.00 COMMENT '归一化分数上限（含）',
  `title` VARCHAR(100) NOT NULL COMMENT '结果名称',
  `subtitle` VARCHAR(150) DEFAULT NULL COMMENT '副标题',
  `narrative` TEXT NOT NULL COMMENT '结果画像文案',
  `advice` VARCHAR(500) DEFAULT NULL COMMENT '温柔建议',
  `tags_json` JSON DEFAULT NULL COMMENT '标签 JSON 数组',
  `illustration_key` VARCHAR(100) DEFAULT NULL COMMENT '前端插画资源 key',
  `share_title` VARCHAR(150) DEFAULT NULL COMMENT '分享标题',
  `status` TINYINT UNSIGNED NOT NULL DEFAULT 1 COMMENT '状态：0下线，1启用',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_personality_result_profile` (`version_id`, `code`),
  KEY `idx_personality_result_match` (`version_id`, `primary_dimension_id`, `status`),
  CONSTRAINT `fk_personality_result_version`
    FOREIGN KEY (`version_id`) REFERENCES `personality_test_version` (`id`),
  CONSTRAINT `fk_personality_result_dimension`
    FOREIGN KEY (`primary_dimension_id`) REFERENCES `personality_dimension` (`id`),
  CONSTRAINT `ck_personality_result_score_range` CHECK (`min_score` >= 0 AND `max_score` <= 100 AND `min_score` <= `max_score`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='人格测试结果模板';

-- 7. 单次作答会话。idempotency_key 防止前端重试时创建重复会话。
CREATE TABLE IF NOT EXISTS `personality_attempt` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  `attempt_no` CHAR(26) NOT NULL COMMENT '对外会话 ID，建议 ULID',
  `user_id` BIGINT UNSIGNED NOT NULL COMMENT 'wx_mini_user.id',
  `test_id` BIGINT UNSIGNED NOT NULL COMMENT 'personality_test.id',
  `test_version_id` BIGINT UNSIGNED NOT NULL COMMENT '作答时冻结的版本 ID',
  `question_count` TINYINT UNSIGNED NOT NULL COMMENT '本次题数',
  `status` TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '状态：0作答中，1已完成，2已过期，3已放弃',
  `idempotency_key` VARCHAR(64) DEFAULT NULL COMMENT '创建会话的幂等键',
  `score_json` JSON DEFAULT NULL COMMENT '各维度最终得分，例如 {"BOUNDARY":87.5}',
  `result_profile_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '命中的结果模板 ID',
  `started_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '开始时间',
  `submitted_at` DATETIME DEFAULT NULL COMMENT '提交完成时间',
  `expires_at` DATETIME NOT NULL COMMENT '过期时间，建议创建后 30 分钟',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_personality_attempt_no` (`attempt_no`),
  UNIQUE KEY `uk_personality_attempt_idempotency` (`user_id`, `idempotency_key`),
  KEY `idx_personality_attempt_user_history` (`user_id`, `status`, `submitted_at`),
  KEY `idx_personality_attempt_expire` (`status`, `expires_at`),
  CONSTRAINT `fk_personality_attempt_user`
    FOREIGN KEY (`user_id`) REFERENCES `wx_mini_user` (`id`),
  CONSTRAINT `fk_personality_attempt_test`
    FOREIGN KEY (`test_id`) REFERENCES `personality_test` (`id`),
  CONSTRAINT `fk_personality_attempt_version`
    FOREIGN KEY (`test_version_id`) REFERENCES `personality_test_version` (`id`),
  CONSTRAINT `fk_personality_attempt_result_profile`
    FOREIGN KEY (`result_profile_id`) REFERENCES `personality_result_profile` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户人格测试作答会话';

-- 8. 本次会话题目与答案快照。question_snapshot_json 中保存题干、选项顺序和内部评分，保证可复算。
CREATE TABLE IF NOT EXISTS `personality_attempt_question` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  `attempt_id` BIGINT UNSIGNED NOT NULL COMMENT 'personality_attempt.id',
  `question_id` BIGINT UNSIGNED NOT NULL COMMENT '原始题目 ID',
  `position` TINYINT UNSIGNED NOT NULL COMMENT '本次第几题，从 1 开始',
  `question_snapshot_json` JSON NOT NULL COMMENT '题干、选项顺序与计分权重快照',
  `answered_option_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '用户选中的原始选项 ID',
  `answered_option_code` CHAR(1) DEFAULT NULL COMMENT '用户选项编码快照',
  `answered_at` DATETIME DEFAULT NULL COMMENT '答题时间',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_personality_attempt_question_position` (`attempt_id`, `position`),
  UNIQUE KEY `uk_personality_attempt_question_source` (`attempt_id`, `question_id`),
  KEY `idx_personality_attempt_question_answer` (`attempt_id`, `answered_at`),
  CONSTRAINT `fk_personality_attempt_question_attempt`
    FOREIGN KEY (`attempt_id`) REFERENCES `personality_attempt` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_personality_attempt_question_question`
    FOREIGN KEY (`question_id`) REFERENCES `personality_question` (`id`),
  CONSTRAINT `fk_personality_attempt_question_option`
    FOREIGN KEY (`answered_option_id`) REFERENCES `personality_option` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='人格测试会话题目与作答快照';

-- 9. 最终报告。此表只在会话完成时创建一次；分享页只读取本表快照，不暴露原始答案。
CREATE TABLE IF NOT EXISTS `personality_report` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  `report_no` CHAR(26) NOT NULL COMMENT '对外报告 ID，建议 ULID',
  `attempt_id` BIGINT UNSIGNED NOT NULL COMMENT 'personality_attempt.id',
  `user_id` BIGINT UNSIGNED NOT NULL COMMENT 'wx_mini_user.id',
  `result_code` VARCHAR(64) NOT NULL COMMENT '结果编码快照',
  `report_snapshot_json` JSON NOT NULL COMMENT '完整展示报告快照',
  `share_token` CHAR(32) NOT NULL COMMENT '分享随机 token',
  `view_count` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '分享报告浏览数',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '生成时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_personality_report_no` (`report_no`),
  UNIQUE KEY `uk_personality_report_attempt` (`attempt_id`),
  UNIQUE KEY `uk_personality_report_share_token` (`share_token`),
  KEY `idx_personality_report_user_created` (`user_id`, `created_at`),
  CONSTRAINT `fk_personality_report_attempt`
    FOREIGN KEY (`attempt_id`) REFERENCES `personality_attempt` (`id`),
  CONSTRAINT `fk_personality_report_user`
    FOREIGN KEY (`user_id`) REFERENCES `wx_mini_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='人格测试最终报告';

-- 可选种子数据：创建测试主体。插入 version 后，将 personality_test.current_version_id 更新为其 ID。
INSERT INTO `personality_test` (`code`, `title`, `description`, `question_count`, `daily_limit`, `status`)
VALUES ('worker_personality', '你的打工人人格是什么？', '3 分钟生成你的职场隐藏属性', 8, 3, 1)
ON DUPLICATE KEY UPDATE
  `title` = VALUES(`title`),
  `description` = VALUES(`description`),
  `question_count` = VALUES(`question_count`),
  `daily_limit` = VALUES(`daily_limit`),
  `status` = VALUES(`status`);

INSERT INTO `personality_dimension` (`code`, `name`, `description`, `sort`, `status`)
VALUES
  ('DRIVE', '任务驱动', '对目标、节奏与交付的投入度', 10, 1),
  ('BOUNDARY', '边界感', '维护工作与生活边界的倾向', 20, 1),
  ('ENERGY', '能量守恒', '用休息和节奏调节能量的倾向', 30, 1),
  ('CREATIVE', '野路子创造力', '以新方法解决问题的倾向', 40, 1)
ON DUPLICATE KEY UPDATE
  `name` = VALUES(`name`),
  `description` = VALUES(`description`),
  `sort` = VALUES(`sort`),
  `status` = VALUES(`status`);
