-- Migration: Renomeia tabela incidents para zeek_alerts (padrão alinhado a suricata_alerts/snort_alerts)
-- Executar em bancos que já possuem incidents. Para instalação nova, use o iot_edu.sql atualizado.

-- Verificar se incidents existe e renomear para zeek_alerts
-- Se zeek_alerts já existir (de instalação anterior), fazer merge ou substituir conforme necessário
RENAME TABLE incidents TO zeek_alerts;
