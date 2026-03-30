-- Corrigir constraint único em pf_id para permitir mesmo pf_id em diferentes instituições
-- Remove o índice único atual em pf_id e cria um índice único composto (pf_id, institution_id)

-- Remover índice único antigo em pf_id se existir
ALTER TABLE `pfsense_firewall_rules` 
DROP INDEX `ix_pfsense_firewall_rules_pf_id` IF EXISTS;

-- Remover constraint único se existir como constraint nomeada
-- (pode não existir se foi criado como índice único)
-- ALTER TABLE `pfsense_firewall_rules` DROP INDEX `pf_id` IF EXISTS;

-- Criar índice único composto (pf_id, institution_id)
-- Isso permite que diferentes instituições tenham regras com o mesmo pf_id
ALTER TABLE `pfsense_firewall_rules` 
ADD UNIQUE INDEX `idx_pf_id_institution_unique` (`pf_id`, `institution_id`);

-- Manter índice simples em pf_id para buscas rápidas (sem unique)
ALTER TABLE `pfsense_firewall_rules` 
ADD INDEX `idx_pf_id` (`pf_id`);

