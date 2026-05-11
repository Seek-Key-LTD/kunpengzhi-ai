-- GraphRAG Database Schema for MySQL HeatWave

USE river;

-- 1. 文本块向量存储表
CREATE TABLE IF NOT EXISTS page_chunks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    page_id INT UNSIGNED NOT NULL,
    chunk_index INT NOT NULL,
    content TEXT NOT NULL,
    embedding JSON NOT NULL COMMENT 'Vector embedding (1024 dimensions)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (page_id) REFERENCES pages(id) ON DELETE CASCADE,
    INDEX idx_page (page_id),
    FULLTEXT INDEX idx_content (content)
);

-- 2. 多维标签表
CREATE TABLE IF NOT EXISTS page_tags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    page_id INT UNSIGNED NOT NULL,
    tag_category VARCHAR(50) NOT NULL COMMENT 'time/geography/theme/person/concept',
    tag_value VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_page_tag (page_id, tag_category, tag_value),
    FOREIGN KEY (page_id) REFERENCES pages(id) ON DELETE CASCADE,
    INDEX idx_category (tag_category),
    INDEX idx_value (tag_value)
);

-- 3. 实体关系表（知识图谱基础）
CREATE TABLE IF NOT EXISTS entity_relations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    source_entity VARCHAR(100) NOT NULL,
    source_type VARCHAR(50) NOT NULL COMMENT 'person/location/event/concept',
    target_entity VARCHAR(100) NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    relation_type VARCHAR(50) NOT NULL COMMENT 'mentioned_in/influenced/preceded_by',
    page_id INT UNSIGNED NOT NULL,
    confidence FLOAT DEFAULT 0.9,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (page_id) REFERENCES pages(id) ON DELETE CASCADE,
    INDEX idx_source (source_entity),
    INDEX idx_target (target_entity),
    INDEX idx_relation (relation_type),
    UNIQUE KEY uk_entity_relation (source_entity, target_entity, relation_type, page_id)
);

-- 4. 知识点拆解表
CREATE TABLE IF NOT EXISTS knowledge_points (
    kp_id VARCHAR(50) NOT NULL PRIMARY KEY COMMENT 'KP-01-001 format',
    title VARCHAR(255) NOT NULL,
    summary TEXT NOT NULL,
    parent_kp_id VARCHAR(50) DEFAULT NULL,
    page_id INT UNSIGNED NOT NULL,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (page_id) REFERENCES pages(id) ON DELETE CASCADE,
    INDEX idx_parent (parent_kp_id)
);

-- 5. 诠释学注释表
CREATE TABLE IF NOT EXISTS annotations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    page_id INT UNSIGNED NOT NULL,
    annotation_type VARCHAR(50) NOT NULL COMMENT 'background/cross-reference/interpretation',
    content TEXT NOT NULL,
    related_pages JSON COMMENT 'Array of related page IDs',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (page_id) REFERENCES pages(id) ON DELETE CASCADE,
    INDEX idx_type (annotation_type)
);
