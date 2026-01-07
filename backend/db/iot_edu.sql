-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Tempo de geração: 07/10/2025 às 01:22
-- Versão do servidor: 10.4.32-MariaDB
-- Versão do PHP: 8.2.12

START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Banco de dados: `iot_edu`
--

-- --------------------------------------------------------

--
-- Estrutura para tabela `blocking_feedback_history`
--

CREATE TABLE `blocking_feedback_history` (
  `id` int(11) NOT NULL,
  `dhcp_mapping_id` int(11) NOT NULL COMMENT 'ID do mapeamento DHCP',
  `user_feedback` text DEFAULT NULL COMMENT 'Feedback detalhado do usuário',
  `problem_resolved` tinyint(1) DEFAULT NULL COMMENT 'NULL = não respondido, TRUE = resolvido, FALSE = não resolvido',
  `feedback_date` datetime DEFAULT NULL COMMENT 'Data/hora do feedback',
  `feedback_by` varchar(100) DEFAULT NULL COMMENT 'Nome/identificação do usuário que forneceu o feedback',
  `admin_notes` text DEFAULT NULL COMMENT 'Anotações da equipe de rede sobre o feedback',
  `admin_review_date` datetime DEFAULT NULL COMMENT 'Data/hora da revisão administrativa',
  `admin_reviewed_by` varchar(100) DEFAULT NULL COMMENT 'Quem revisou o feedback',
  `status` enum('PENDING','REVIEWED','ACTION_REQUIRED') NOT NULL COMMENT 'Status atual do feedback',
  `created_at` datetime DEFAULT NULL COMMENT 'Data/hora de criação',
  `updated_at` datetime DEFAULT NULL COMMENT 'Data/hora da última atualização'
) ;

-- --------------------------------------------------------

--
-- Estrutura para tabela `dhcp_servers`
--

CREATE TABLE `dhcp_servers` (
  `id` int(11) NOT NULL,
  `server_id` varchar(50) NOT NULL,
  `interface` varchar(50) NOT NULL,
  `enable` tinyint(1) DEFAULT NULL,
  `range_from` varchar(15) DEFAULT NULL,
  `range_to` varchar(15) DEFAULT NULL,
  `domain` varchar(255) DEFAULT NULL,
  `gateway` varchar(15) DEFAULT NULL,
  `dnsserver` varchar(15) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL
) ;

-- --------------------------------------------------------

--
-- Estrutura para tabela `dhcp_static_mappings`
--

CREATE TABLE `dhcp_static_mappings` (
  `id` int(11) NOT NULL,
  `server_id` int(11) NOT NULL,
  `pf_id` int(11) NOT NULL,
  `mac` varchar(17) NOT NULL,
  `ipaddr` varchar(15) NOT NULL,
  `cid` varchar(255) DEFAULT NULL,
  `hostname` varchar(255) DEFAULT NULL,
  `descr` text DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `is_blocked` tinyint(1) DEFAULT 0,
  `reason` text DEFAULT NULL
) ;

-- --------------------------------------------------------

--
-- Estrutura para tabela `pfsense_aliases`
--

CREATE TABLE `pfsense_aliases` (
  `id` int(11) NOT NULL,
  `pf_id` int(11) DEFAULT NULL COMMENT 'ID do alias no pfSense',
  `name` varchar(255) NOT NULL COMMENT 'Nome do alias',
  `alias_type` varchar(50) NOT NULL COMMENT 'Tipo do alias (host, network, port, url, urltable)',
  `descr` text DEFAULT NULL COMMENT 'Descrição do alias',
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL
) ;

-- --------------------------------------------------------

--
-- Estrutura para tabela `pfsense_alias_addresses`
--

CREATE TABLE `pfsense_alias_addresses` (
  `id` int(11) NOT NULL,
  `alias_id` int(11) NOT NULL,
  `address` varchar(255) NOT NULL COMMENT 'Endereço IP, rede ou porta',
  `detail` text DEFAULT NULL COMMENT 'Detalhes do endereço',
  `created_at` datetime DEFAULT NULL
) ;

-- --------------------------------------------------------

--
-- Estrutura para tabela `pfsense_firewall_rules`
--

CREATE TABLE `pfsense_firewall_rules` (
  `id` int(11) NOT NULL,
  `pf_id` int(11) NOT NULL,
  `type` varchar(32) DEFAULT NULL,
  `interface` varchar(255) DEFAULT NULL,
  `ipprotocol` varchar(16) DEFAULT NULL,
  `protocol` varchar(16) DEFAULT NULL,
  `icmptype` varchar(64) DEFAULT NULL,
  `source` varchar(255) DEFAULT NULL,
  `source_port` varchar(64) DEFAULT NULL,
  `destination` varchar(255) DEFAULT NULL,
  `destination_port` varchar(64) DEFAULT NULL,
  `descr` text DEFAULT NULL,
  `disabled` tinyint(1) DEFAULT NULL,
  `log` tinyint(1) DEFAULT NULL,
  `tag` varchar(128) DEFAULT NULL,
  `statetype` varchar(64) DEFAULT NULL,
  `tcp_flags_any` tinyint(1) DEFAULT NULL,
  `tcp_flags_out_of` varchar(64) DEFAULT NULL,
  `tcp_flags_set` varchar(64) DEFAULT NULL,
  `gateway` varchar(64) DEFAULT NULL,
  `sched` varchar(64) DEFAULT NULL,
  `dnpipe` varchar(64) DEFAULT NULL,
  `pdnpipe` varchar(64) DEFAULT NULL,
  `defaultqueue` varchar(64) DEFAULT NULL,
  `ackqueue` varchar(64) DEFAULT NULL,
  `floating` tinyint(1) DEFAULT NULL,
  `quick` tinyint(1) DEFAULT NULL,
  `direction` varchar(32) DEFAULT NULL,
  `tracker` int(11) DEFAULT NULL,
  `associated_rule_id` int(11) DEFAULT NULL,
  `created_time` datetime DEFAULT NULL,
  `created_by` varchar(255) DEFAULT NULL,
  `updated_time` datetime DEFAULT NULL,
  `updated_by` varchar(255) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL
) ;

-- --------------------------------------------------------

--
-- Estrutura para tabela `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `email` varchar(255) NOT NULL,
  `nome` varchar(255) DEFAULT NULL,
  `instituicao` varchar(255) DEFAULT NULL,
  `ultimo_login` datetime DEFAULT NULL,
  `permission` enum('USER','MANAGER') NOT NULL DEFAULT 'USER',
  `google_sub` varchar(255) DEFAULT NULL,
  `picture` varchar(512) DEFAULT NULL
) ;

-- --------------------------------------------------------

--
-- Estrutura para tabela `user_device_assignments`
--

CREATE TABLE `user_device_assignments` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `device_id` int(11) NOT NULL,
  `assigned_at` datetime DEFAULT NULL,
  `assigned_by` int(11) DEFAULT NULL,
  `notes` text DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT NULL
) ;

-- --------------------------------------------------------

--
-- Estrutura para tabela `zeek_incidents`
--

CREATE TABLE `zeek_incidents` (
  `id` int(11) NOT NULL,
  `device_ip` varchar(15) NOT NULL COMMENT 'IP do dispositivo envolvido',
  `device_name` varchar(255) DEFAULT NULL COMMENT 'Nome do dispositivo',
  `incident_type` varchar(255) NOT NULL COMMENT 'Tipo de incidente',
  `severity` enum('LOW','MEDIUM','HIGH','CRITICAL') NOT NULL COMMENT 'Nível de severidade',
  `status` enum('NEW','INVESTIGATING','RESOLVED','FALSE_POSITIVE','ESCALATED') NOT NULL COMMENT 'Status do incidente',
  `description` text NOT NULL COMMENT 'Descrição detalhada',
  `detected_at` datetime NOT NULL COMMENT 'Data/hora da detecção',
  `zeek_log_type` enum('HTTP','DNS','CONN','SSL','FILES','WEIRD','NOTICE') NOT NULL COMMENT 'Tipo de log do Zeek',
  `raw_log_data` text DEFAULT NULL COMMENT 'Dados brutos do log em JSON',
  `action_taken` text DEFAULT NULL COMMENT 'Ação tomada',
  `assigned_to` int(11) DEFAULT NULL COMMENT 'Usuário responsável',
  `notes` text DEFAULT NULL COMMENT 'Observações adicionais',
  `created_at` datetime DEFAULT NULL COMMENT 'Data de criação',
  `updated_at` datetime DEFAULT NULL COMMENT 'Data de atualização'
) ;

--
-- Índices para tabelas despejadas
--

--
-- Índices de tabela `blocking_feedback_history`
--
ALTER TABLE `blocking_feedback_history`
  ADD PRIMARY KEY (`id`),
  ADD KEY `ix_blocking_feedback_history_id` (`id`),
  ADD KEY `idx_feedback_status` (`status`),
  ADD KEY `idx_feedback_date` (`feedback_date`),
  ADD KEY `idx_feedback_by` (`feedback_by`),
  ADD KEY `idx_feedback_dhcp_mapping` (`dhcp_mapping_id`),
  ADD KEY `idx_feedback_reviewed_by` (`admin_reviewed_by`);

--
-- Índices de tabela `dhcp_servers`
--
ALTER TABLE `dhcp_servers`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `ix_dhcp_servers_server_id` (`server_id`),
  ADD KEY `ix_dhcp_servers_id` (`id`);

--
-- Índices de tabela `dhcp_static_mappings`
--
ALTER TABLE `dhcp_static_mappings`
  ADD PRIMARY KEY (`id`),
  ADD KEY `server_id` (`server_id`),
  ADD KEY `ix_dhcp_static_mappings_ipaddr` (`ipaddr`),
  ADD KEY `ix_dhcp_static_mappings_id` (`id`),
  ADD KEY `ix_dhcp_static_mappings_mac` (`mac`);

--
-- Índices de tabela `pfsense_aliases`
--
ALTER TABLE `pfsense_aliases`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `ix_pfsense_aliases_name` (`name`),
  ADD UNIQUE KEY `ix_pfsense_aliases_pf_id` (`pf_id`),
  ADD KEY `ix_pfsense_aliases_id` (`id`);

--
-- Índices de tabela `pfsense_alias_addresses`
--
ALTER TABLE `pfsense_alias_addresses`
  ADD PRIMARY KEY (`id`),
  ADD KEY `alias_id` (`alias_id`),
  ADD KEY `ix_pfsense_alias_addresses_id` (`id`);

--
-- Índices de tabela `pfsense_firewall_rules`
--
ALTER TABLE `pfsense_firewall_rules`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `ix_pfsense_firewall_rules_pf_id` (`pf_id`),
  ADD KEY `ix_pfsense_firewall_rules_id` (`id`);

--
-- Índices de tabela `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `ix_users_email` (`email`),
  ADD UNIQUE KEY `google_sub` (`google_sub`),
  ADD KEY `ix_users_id` (`id`);

--
-- Índices de tabela `user_device_assignments`
--
ALTER TABLE `user_device_assignments`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `idx_user_device_unique` (`user_id`,`device_id`),
  ADD KEY `device_id` (`device_id`),
  ADD KEY `assigned_by` (`assigned_by`),
  ADD KEY `ix_user_device_assignments_id` (`id`);

--
-- Índices de tabela `zeek_incidents`
--
ALTER TABLE `zeek_incidents`
  ADD PRIMARY KEY (`id`),
  ADD KEY `assigned_to` (`assigned_to`),
  ADD KEY `idx_incident_severity` (`severity`),
  ADD KEY `ix_zeek_incidents_device_ip` (`device_ip`),
  ADD KEY `ix_zeek_incidents_id` (`id`),
  ADD KEY `idx_incident_status` (`status`),
  ADD KEY `idx_incident_detected_at` (`detected_at`),
  ADD KEY `idx_incident_device_ip` (`device_ip`),
  ADD KEY `idx_incident_log_type` (`zeek_log_type`),
  ADD KEY `idx_incident_device_severity` (`device_ip`,`severity`);

--
-- AUTO_INCREMENT para tabelas despejadas
--

--
-- AUTO_INCREMENT de tabela `blocking_feedback_history`
--
ALTER TABLE `blocking_feedback_history`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `dhcp_servers`
--
ALTER TABLE `dhcp_servers`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `dhcp_static_mappings`
--
ALTER TABLE `dhcp_static_mappings`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `pfsense_aliases`
--
ALTER TABLE `pfsense_aliases`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `pfsense_alias_addresses`
--
ALTER TABLE `pfsense_alias_addresses`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `pfsense_firewall_rules`
--
ALTER TABLE `pfsense_firewall_rules`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `user_device_assignments`
--
ALTER TABLE `user_device_assignments`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `zeek_incidents`
--
ALTER TABLE `zeek_incidents`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- Restrições para tabelas despejadas
--

--
-- Restrições para tabelas `blocking_feedback_history`
--
ALTER TABLE `blocking_feedback_history`
  ADD CONSTRAINT `blocking_feedback_history_ibfk_1` FOREIGN KEY (`dhcp_mapping_id`) REFERENCES `dhcp_static_mappings` (`id`);

--
-- Restrições para tabelas `dhcp_static_mappings`
--
ALTER TABLE `dhcp_static_mappings`
  ADD CONSTRAINT `dhcp_static_mappings_ibfk_1` FOREIGN KEY (`server_id`) REFERENCES `dhcp_servers` (`id`);

--
-- Restrições para tabelas `pfsense_alias_addresses`
--
ALTER TABLE `pfsense_alias_addresses`
  ADD CONSTRAINT `pfsense_alias_addresses_ibfk_1` FOREIGN KEY (`alias_id`) REFERENCES `pfsense_aliases` (`id`);

--
-- Restrições para tabelas `user_device_assignments`
--
ALTER TABLE `user_device_assignments`
  ADD CONSTRAINT `user_device_assignments_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  ADD CONSTRAINT `user_device_assignments_ibfk_2` FOREIGN KEY (`device_id`) REFERENCES `dhcp_static_mappings` (`id`),
  ADD CONSTRAINT `user_device_assignments_ibfk_3` FOREIGN KEY (`assigned_by`) REFERENCES `users` (`id`);

--
-- Restrições para tabelas `zeek_incidents`
--
ALTER TABLE `zeek_incidents`
  ADD CONSTRAINT `zeek_incidents_ibfk_1` FOREIGN KEY (`assigned_to`) REFERENCES `users` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
