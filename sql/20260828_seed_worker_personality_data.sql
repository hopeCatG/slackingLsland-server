-- 打工人人格测试首发题库数据（MySQL 8.0+）
-- 前置条件：personality_test 中存在 code=worker_personality；
--           personality_dimension 中存在 DRIVE / BOUNDARY / ENERGY / CREATIVE。
-- 本脚本可重复执行，不会重复生成版本、题目、选项或结果模板。

SET NAMES utf8mb4;
START TRANSACTION;

SET @test_id := (
  SELECT `id` FROM `personality_test`
  WHERE `code` = 'worker_personality'
  LIMIT 1
);

-- 1. 创建/更新首发版本，并取得版本 ID。
INSERT INTO `personality_test_version`
  (`test_id`, `version_no`, `algorithm_version`, `status`, `published_at`)
VALUES
  (@test_id, 'v1.0.0', 'v1', 1, NOW())
ON DUPLICATE KEY UPDATE
  `id` = LAST_INSERT_ID(`id`),
  `algorithm_version` = VALUES(`algorithm_version`),
  `status` = 1,
  `published_at` = COALESCE(`published_at`, VALUES(`published_at`));

SET @version_id := LAST_INSERT_ID();

UPDATE `personality_test`
SET `current_version_id` = @version_id,
    `question_count` = 8,
    `daily_limit` = 3,
    `status` = 1
WHERE `id` = @test_id;

-- 2. 初始化 12 道题。
INSERT INTO `personality_question`
  (`version_id`, `code`, `stem`, `sort`, `status`)
VALUES
  (@version_id, 'Q01', '周一 9:00，你的「开机动画」是？', 10, 1),
  (@version_id, 'Q02', '领导发来「在吗？」你会？', 20, 1),
  (@version_id, 'Q03', '突然被塞进一个「很急」的需求？', 30, 1),
  (@version_id, 'Q04', '下午 3 点电量告急，你的补给方式？', 40, 1),
  (@version_id, 'Q05', '开会 40 分钟后，话题开始绕圈？', 50, 1),
  (@version_id, 'Q06', '同事说「这活怎么又变了」？', 60, 1),
  (@version_id, 'Q07', '下班前 5 分钟收到新消息？', 70, 1),
  (@version_id, 'Q08', '面对重复性工作，你通常？', 80, 1),
  (@version_id, 'Q09', '项目临近截止，群里开始「@所有人」？', 90, 1),
  (@version_id, 'Q10', '你的工位桌面更像？', 100, 1),
  (@version_id, 'Q11', '当你真的搞不定时？', 110, 1),
  (@version_id, 'Q12', '你希望同事怎样形容你？', 120, 1)
ON DUPLICATE KEY UPDATE
  `stem` = VALUES(`stem`),
  `sort` = VALUES(`sort`),
  `status` = VALUES(`status`);

-- 3. 初始化 48 个选项及计分权重。
-- 选项通过题目 code 和维度 code 反查主键，不依赖数据库中的具体 ID。
INSERT INTO `personality_option`
  (`question_id`, `code`, `content`, `dimension_id`, `score`, `sort`, `status`)
SELECT
  q.`id`, seed.`option_code`, seed.`content`, d.`id`, seed.`score`, seed.`sort`, 1
FROM (
  SELECT 'Q01' qcode, 'A' option_code, '待办已排好，开冲' content, 'DRIVE' dimension_code, 3 score, 10 sort
  UNION ALL SELECT 'Q01', 'B', '先看优先级，别急', 'BOUNDARY', 3, 20
  UNION ALL SELECT 'Q01', 'C', '咖啡到位再启动', 'ENERGY', 3, 30
  UNION ALL SELECT 'Q01', 'D', '先找个小工具省力', 'CREATIVE', 3, 40

  UNION ALL SELECT 'Q02', 'A', '秒回并确认要点', 'DRIVE', 2, 10
  UNION ALL SELECT 'Q02', 'B', '回：在，10 分钟后给你答复', 'BOUNDARY', 3, 20
  UNION ALL SELECT 'Q02', 'C', '深呼吸，组织语言', 'ENERGY', 2, 30
  UNION ALL SELECT 'Q02', 'D', '在的，雷达已开启——然后问需求', 'CREATIVE', 2, 40

  UNION ALL SELECT 'Q03', 'A', '拆任务、拉人、开干', 'DRIVE', 3, 10
  UNION ALL SELECT 'Q03', 'B', '先问截止时间和验收标准', 'BOUNDARY', 3, 20
  UNION ALL SELECT 'Q03', 'C', '先稳住：我处理一下', 'ENERGY', 2, 30
  UNION ALL SELECT 'Q03', 'D', '找模板、自动化或旧方案抄近路', 'CREATIVE', 3, 40

  UNION ALL SELECT 'Q04', 'A', '列完剩余任务再休息', 'DRIVE', 2, 10
  UNION ALL SELECT 'Q04', 'B', '关 15 分钟通知，专注收尾', 'BOUNDARY', 3, 20
  UNION ALL SELECT 'Q04', 'C', '走两分钟，给 CPU 散热', 'ENERGY', 3, 30
  UNION ALL SELECT 'Q04', 'D', '做个表格或脚本让活少一点', 'CREATIVE', 3, 40

  UNION ALL SELECT 'Q05', 'A', '记下结论和负责人', 'DRIVE', 3, 10
  UNION ALL SELECT 'Q05', 'B', '提议定个结论和下一步', 'BOUNDARY', 3, 20
  UNION ALL SELECT 'Q05', 'C', '悄悄喝水，保持人类在线', 'ENERGY', 3, 30
  UNION ALL SELECT 'Q05', 'D', '把散点画成图，试图召唤共识', 'CREATIVE', 3, 40

  UNION ALL SELECT 'Q06', 'A', '调整计划，先守住关键交付', 'DRIVE', 3, 10
  UNION ALL SELECT 'Q06', 'B', '说明影响，请对方确认优先级', 'BOUNDARY', 3, 20
  UNION ALL SELECT 'Q06', 'C', '先共情一句：确实有点班味', 'ENERGY', 2, 30
  UNION ALL SELECT 'Q06', 'D', '说不定能换个更省事的做法', 'CREATIVE', 3, 40

  UNION ALL SELECT 'Q07', 'A', '能做的先推进一小步', 'DRIVE', 2, 10
  UNION ALL SELECT 'Q07', 'B', '回复收到，明早几点反馈', 'BOUNDARY', 3, 20
  UNION ALL SELECT 'Q07', 'C', '非紧急就交给明天的我', 'ENERGY', 3, 30
  UNION ALL SELECT 'Q07', 'D', '先设自动提醒，避免明早失忆', 'CREATIVE', 2, 40

  UNION ALL SELECT 'Q08', 'A', '做成清单，稳定批量完成', 'DRIVE', 3, 10
  UNION ALL SELECT 'Q08', 'B', '划定处理时段，别全天被打断', 'BOUNDARY', 3, 20
  UNION ALL SELECT 'Q08', 'C', '交替做轻重任务，避免耗空', 'ENERGY', 3, 30
  UNION ALL SELECT 'Q08', 'D', '邪修一下：想办法自动化', 'CREATIVE', 3, 40

  UNION ALL SELECT 'Q09', 'A', '主动同步进度和风险', 'DRIVE', 3, 10
  UNION ALL SELECT 'Q09', 'B', '明确我负责的范围与依赖', 'BOUNDARY', 3, 20
  UNION ALL SELECT 'Q09', 'C', '先做最重要的一件，拒绝慌张', 'ENERGY', 3, 30
  UNION ALL SELECT 'Q09', 'D', '拉出看板，让卡点无处藏身', 'CREATIVE', 2, 40

  UNION ALL SELECT 'Q10', 'A', '指挥台：资料都在手边', 'DRIVE', 2, 10
  UNION ALL SELECT 'Q10', 'B', '结界：工作物与私人区分开', 'BOUNDARY', 3, 20
  UNION ALL SELECT 'Q10', 'C', '补给站：水杯零食充电线齐全', 'ENERGY', 3, 30
  UNION ALL SELECT 'Q10', 'D', '实验室：便利贴和奇怪工具很多', 'CREATIVE', 3, 40

  UNION ALL SELECT 'Q11', 'A', '提早求助，并带上已尝试方案', 'DRIVE', 3, 10
  UNION ALL SELECT 'Q11', 'B', '说明资源缺口，请协商排期', 'BOUNDARY', 3, 20
  UNION ALL SELECT 'Q11', 'C', '允许自己暂停 5 分钟再回来', 'ENERGY', 3, 30
  UNION ALL SELECT 'Q11', 'D', '找跨团队同事换个视角', 'CREATIVE', 3, 40

  UNION ALL SELECT 'Q12', 'A', '交给 TA，我放心', 'DRIVE', 3, 10
  UNION ALL SELECT 'Q12', 'B', '靠谱又有边界', 'BOUNDARY', 3, 20
  UNION ALL SELECT 'Q12', 'C', '和 TA 协作不累', 'ENERGY', 3, 30
  UNION ALL SELECT 'Q12', 'D', '总能想出办法', 'CREATIVE', 3, 40
) AS seed
JOIN `personality_question` q
  ON q.`version_id` = @version_id AND q.`code` = seed.`qcode`
JOIN `personality_dimension` d
  ON d.`code` = seed.`dimension_code`
ON DUPLICATE KEY UPDATE
  `content` = VALUES(`content`),
  `dimension_id` = VALUES(`dimension_id`),
  `score` = VALUES(`score`),
  `sort` = VALUES(`sort`),
  `status` = VALUES(`status`);

-- 4. 初始化 6 种人格结果模板。
INSERT INTO `personality_result_profile`
  (`version_id`, `code`, `primary_dimension_id`, `min_score`, `max_score`, `title`, `subtitle`,
   `narrative`, `advice`, `tags_json`, `illustration_key`, `share_title`, `status`)
SELECT
  @version_id, seed.`profile_code`, d.`id`, 0.00, 100.00,
  seed.`title`, seed.`subtitle`, seed.`narrative`, seed.`advice`,
  seed.`tags_json`, seed.`illustration_key`, seed.`share_title`, 1
FROM (
  SELECT
    'STEADY_ENGINE' profile_code, 'DRIVE' dimension_code,
    '稳定发动机' title, '交付到站，请签收' subtitle,
    '你不是在上班，你是在把混乱排成队。群里一声「谁来跟」，你已经默默开工。' narrative,
    '给自己也排一个不被打扰的 30 分钟。' advice,
    JSON_ARRAY('交付可靠', '行动派', '稳稳接住') tags_json,
    '🚂' illustration_key, '我的打工人格是「稳定发动机」' share_title
  UNION ALL SELECT
    'BOUNDARY_MASTER', 'BOUNDARY', '下班结界师', '已离线，但很靠谱',
    '你不靠 24 小时待机证明认真；你靠清晰优先级把事情办漂亮。',
    '继续保持同步节奏，边界会让协作更轻松。',
    JSON_ARRAY('边界清晰', '拒绝内耗', '沟通到位'), '🪄', '我的打工人格是「下班结界师」'
  UNION ALL SELECT
    'FISHING_STRATEGIST', 'ENERGY', '摸鱼战略家', '能量管理，拒绝空转',
    '你不是消失，是在给 CPU 散热。该冲时冲，该缓冲时也知道留一口气。',
    '给摸鱼设一个恢复目的：喝水、走两分钟、再回来收尾。',
    JSON_ARRAY('能量管理', '松弛感', '续航在线'), '🐟', '我的打工人格是「摸鱼战略家」'
  UNION ALL SELECT
    'WILDCARD_SOLVER', 'CREATIVE', '邪修解题官', '正路堵车，换条路到达',
    '别人照 SOP 走，你先看有没有快捷入口；离谱一点，但常常真能成。',
    '把好点子写成步骤，让野路子也能被团队复用。',
    JSON_ARRAY('脑洞在线', '工具达人', '另辟蹊径'), '🛠️', '我的打工人格是「邪修解题官」'
  UNION ALL SELECT
    'CALM_COORDINATOR', 'BOUNDARY', '淡定调度员', '事情很多，先别急',
    '你擅长把「都很急」翻译成「谁最急、先做什么」，混乱到你这里会自动排队。',
    '遇到模糊需求时，先确认截止时间和验收标准。',
    JSON_ARRAY('优先级大师', '情绪稳定', '协作顺滑'), '🧭', '我的打工人格是「淡定调度员」'
  UNION ALL SELECT
    'WARM_TEAMMATE', 'ENERGY', '职场发小体质', '有你在，群聊有温度',
    '你能把「收到」回出人味，也能在别人卡住时递一把梯子。',
    '先照顾好自己的电量，再持续输出情绪价值。',
    JSON_ARRAY('气氛担当', '共情在线', '团队回血'), '🫶', '我的打工人格是「职场发小体质」'
) AS seed
JOIN `personality_dimension` d
  ON d.`code` = seed.`dimension_code`
ON DUPLICATE KEY UPDATE
  `primary_dimension_id` = VALUES(`primary_dimension_id`),
  `min_score` = VALUES(`min_score`),
  `max_score` = VALUES(`max_score`),
  `title` = VALUES(`title`),
  `subtitle` = VALUES(`subtitle`),
  `narrative` = VALUES(`narrative`),
  `advice` = VALUES(`advice`),
  `tags_json` = VALUES(`tags_json`),
  `illustration_key` = VALUES(`illustration_key`),
  `share_title` = VALUES(`share_title`),
  `status` = VALUES(`status`);

COMMIT;

-- 5. 执行结果核对：应返回 1 个版本、12 道题、48 个选项、6 个结果模板。
SELECT
  @test_id AS `test_id`,
  @version_id AS `version_id`,
  (SELECT COUNT(*) FROM `personality_test_version` WHERE `id` = @version_id) AS `version_count`,
  (SELECT COUNT(*) FROM `personality_question` WHERE `version_id` = @version_id) AS `question_count`,
  (SELECT COUNT(*)
     FROM `personality_option` o
     JOIN `personality_question` q ON q.`id` = o.`question_id`
    WHERE q.`version_id` = @version_id) AS `option_count`,
  (SELECT COUNT(*) FROM `personality_result_profile` WHERE `version_id` = @version_id) AS `profile_count`;
