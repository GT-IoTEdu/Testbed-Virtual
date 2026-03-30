-- Adicionar campo institution_id à tabela pfsense_firewall_rules
-- Permite associar regras de firewall a uma instituição específica

ALTER TABLE `pfsense_firewall_rules` 
ADD COLUMN `institution_id` INT(11) NULL DEFAULT NULL 
COMMENT 'ID da instituição/campus ao qual a regra pertence' 
AFTER `updated_by`;

-- Adicionar índice em institution_id para buscas
ALTER TABLE `pfsense_firewall_rules` 
ADD INDEX `idx_institution_id` (`institution_id`);

-- Adicionar foreign key constraint
ALTER TABLE `pfsense_firewall_rules` 
ADD CONSTRAINT `fk_pfsense_firewall_rules_institution` 
FOREIGN KEY (`institution_id`) REFERENCES `institutions` (`id`) 
ON DELETE SET NULL ON UPDATE CASCADE;

