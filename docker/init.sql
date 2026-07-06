-- 初始化数据库（首次启动 MySQL 时自动执行）
-- 如果数据库已存在则跳过

CREATE DATABASE IF NOT EXISTS `ds_platform`
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE `ds_platform`;
