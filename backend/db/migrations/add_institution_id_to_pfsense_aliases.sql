-- Migração: Adicionar coluna institution_id na tabela pfsense_aliases
-- Data: 2025-01-XX
-- Descrição: Adiciona suporte para vincular aliases a instituições/campus

-- Remover índices únicos antigos que não consideram institution_id
ALTER TABLE `pfsense_aliases` 
DROP INDEX IF EXISTS `name`;

ALTER TABLE `pfsense_aliases` 
DROP INDEX IF EXISTS `pf_id`;

-- Adicionar coluna institution_id (nullable para permitir aliases existentes)
ALTER TABLE `pfsense_aliases` 
ADD COLUMN `institution_id` INT(11) NULL DEFAULT NULL 
COMMENT 'ID da instituição/campus ao qual o alias pertence' 
AFTER `descr`;

-- Adicionar índice para melhorar performance de consultas
ALTER TABLE `pfsense_aliases` 
ADD INDEX `idx_institution_id` (`institution_id`);

-- Criar índice único composto (name, institution_id) para permitir mesmo nome em instituições diferentes
ALTER TABLE `pfsense_aliases` 
ADD UNIQUE INDEX `idx_alias_name_institution_unique` (`name`, `institution_id`);

-- Adicionar índice para pf_id (não mais único, pois pode repetir entre instituições)
ALTER TABLE `pfsense_aliases` 
ADD INDEX `idx_pf_id` (`pf_id`);

-- Adicionar chave estrangeira (opcional, pode ser adicionada depois se necessário)
-- ALTER TABLE `pfsense_aliases` 
-- ADD CONSTRAINT `fk_pfsense_alias_institution` 
-- FOREIGN KEY (`institution_id`) REFERENCES `institutions` (`id`) 
-- ON DELETE SET NULL ON UPDATE CASCADE;

-- Nota: A chave estrangeira foi comentada para permitir flexibilidade.
-- Se desejar adicionar, descomente as linhas acima.

