-- Migração: Adicionar coluna institution_id na tabela dhcp_static_mappings
-- Data: 2025-01-XX
-- Descrição: Adiciona suporte para vincular dispositivos a instituições/campus

-- Adicionar coluna institution_id (nullable para permitir dispositivos existentes)
ALTER TABLE `dhcp_static_mappings` 
ADD COLUMN `institution_id` INT(11) NULL DEFAULT NULL 
COMMENT 'ID da instituição/campus ao qual o dispositivo pertence' 
AFTER `descr`;

-- Adicionar índice para melhorar performance de consultas
ALTER TABLE `dhcp_static_mappings` 
ADD INDEX `idx_institution_id` (`institution_id`);

-- Adicionar chave estrangeira (opcional, pode ser adicionada depois se necessário)
-- ALTER TABLE `dhcp_static_mappings` 
-- ADD CONSTRAINT `fk_dhcp_static_mapping_institution` 
-- FOREIGN KEY (`institution_id`) REFERENCES `institutions` (`id`) 
-- ON DELETE SET NULL ON UPDATE CASCADE;

-- Nota: A chave estrangeira foi comentada para permitir flexibilidade.
-- Se desejar adicionar, descomente as linhas acima.

