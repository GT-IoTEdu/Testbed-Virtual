-- Migração: Corrigir constraint única do campo nome na tabela institutions
-- Data: 2025-01-XX
-- Descrição: Permite múltiplas instituições com o mesmo nome em cidades diferentes
--            Remove índice único do campo nome e cria índice único composto (nome, cidade)

-- Remover índice único antigo do campo nome
ALTER TABLE `institutions` 
DROP INDEX IF EXISTS `ix_institutions_nome`;

-- Remover constraint única se existir (pode ter nomes diferentes dependendo do banco)
ALTER TABLE `institutions` 
DROP INDEX IF EXISTS `nome`;

-- Criar índice único composto (nome, cidade) para permitir mesmo nome em cidades diferentes
-- mas impedir duplicatas da mesma instituição na mesma cidade
ALTER TABLE `institutions` 
ADD UNIQUE INDEX `idx_institution_nome_cidade_unique` (`nome`, `cidade`);

-- Adicionar índice simples no campo nome para melhorar performance de consultas
ALTER TABLE `institutions` 
ADD INDEX `idx_institution_nome` (`nome`);

