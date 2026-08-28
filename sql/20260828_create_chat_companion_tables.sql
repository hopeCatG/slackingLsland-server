-- 聊天搭子：本地会话与消息历史。Dify API Key 不进入业务表，统一放 system_config。
CREATE TABLE IF NOT EXISTS `chat_companion_session` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `session_no` VARCHAR(32) NOT NULL COMMENT '对外会话编号',
  `user_id` BIGINT UNSIGNED NOT NULL COMMENT 'wx_mini_user.id',
  `dify_conversation_id` VARCHAR(100) NULL COMMENT 'Dify 会话 ID',
  `topic` VARCHAR(100) NOT NULL COMMENT '吐槽主题',
  `mood` VARCHAR(50) NOT NULL COMMENT '当前情绪',
  `event_detail` VARCHAR(1000) NOT NULL COMMENT '具体事件',
  `title` VARCHAR(100) NOT NULL COMMENT '会话标题',
  `status` TINYINT UNSIGNED NOT NULL DEFAULT 1 COMMENT '1正常 0删除',
  `last_message_at` DATETIME NULL COMMENT '最后消息时间',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_chat_companion_session_no` (`session_no`),
  KEY `idx_chat_companion_user_history` (`user_id`, `status`, `last_message_at`),
  CONSTRAINT `fk_chat_companion_session_user`
    FOREIGN KEY (`user_id`) REFERENCES `wx_mini_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='聊天搭子会话';

CREATE TABLE IF NOT EXISTS `chat_companion_message` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `session_id` BIGINT UNSIGNED NOT NULL COMMENT 'chat_companion_session.id',
  `role` VARCHAR(16) NOT NULL COMMENT 'user/assistant',
  `content` TEXT NOT NULL COMMENT '消息正文',
  `dify_message_id` VARCHAR(100) NULL COMMENT 'Dify 消息 ID',
  `status` TINYINT UNSIGNED NOT NULL DEFAULT 1 COMMENT '1正常 0删除',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_chat_companion_message_list` (`session_id`, `status`, `id`),
  CONSTRAINT `fk_chat_companion_message_session`
    FOREIGN KEY (`session_id`) REFERENCES `chat_companion_session` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='聊天搭子消息';

-- 请把 YOUR_DIFY_APP_API_KEY 替换为 Dify 对话应用的真实 API Key。
INSERT INTO `system_config` (`config_key`, `config_value`, `remark`, `is_enabled`)
VALUES
  ('DIFY_CHAT_BASE_URL', 'http://word.skyblue.chat/v1', '聊天搭子 Dify API 基础地址', 1),
  ('DIFY_CHAT_API_KEY', 'YOUR_DIFY_APP_API_KEY', '聊天搭子 Dify App API Key（仅服务端读取）', 1)
ON DUPLICATE KEY UPDATE
  `remark` = VALUES(`remark`),
  `is_enabled` = VALUES(`is_enabled`);
