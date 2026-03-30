-- Migration: Renomeia tabela zeek_incidents para incidents (padrão alinhado a zeek_alerts/suricata_alerts/snort_alerts)
-- Executar em bancos que já possuem zeek_incidents. Para instalação nova, use o iot_edu.sql atualizado.

-- Renomear tabela (preserva dados e índices)
RENAME TABLE zeek_incidents TO incidents;
