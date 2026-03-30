#!/usr/bin/env python3
"""
Executa a migration: renomeia zeek_alerts -> incidents e cria nova tabela zeek_alerts (estrutura Suricata).
Uso: python -m db.run_migration_split_zeek_incidents
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from db.session import engine


def main():
    with engine.connect() as conn:
        # Verificar se zeek_alerts existe (estrutura antiga = Incident)
        r = conn.execute(text("SHOW TABLES LIKE 'zeek_alerts'"))
        if not r.fetchone():
            r2 = conn.execute(text("SHOW TABLES LIKE 'incidents'"))
            if r2.fetchone():
                # incidents já existe; verificar se zeek_alerts existe
                r3 = conn.execute(text("SHOW TABLES LIKE 'zeek_alerts'"))
                if r3.fetchone():
                    print("Tabelas incidents e zeek_alerts já existem. Nada a fazer.")
                else:
                    # Só criar zeek_alerts
                    conn.execute(text("""
                        CREATE TABLE zeek_alerts (
                          id int(11) NOT NULL AUTO_INCREMENT,
                          institution_id int(11) NOT NULL,
                          detected_at datetime NOT NULL,
                          signature varchar(500) NOT NULL,
                          signature_id varchar(50) DEFAULT NULL,
                          severity enum('LOW','MEDIUM','HIGH','CRITICAL') NOT NULL DEFAULT 'MEDIUM',
                          src_ip varchar(45) DEFAULT NULL,
                          dest_ip varchar(45) DEFAULT NULL,
                          src_port varchar(20) DEFAULT NULL,
                          dest_port varchar(20) DEFAULT NULL,
                          protocol varchar(20) DEFAULT NULL,
                          category varchar(255) DEFAULT NULL,
                          raw_log_data text DEFAULT NULL,
                          processed_at datetime DEFAULT NULL,
                          created_at datetime DEFAULT NULL,
                          updated_at datetime DEFAULT NULL,
                          PRIMARY KEY (id),
                          KEY idx_zeek_alerts_institution_id (institution_id),
                          KEY idx_zeek_alerts_detected_at (detected_at),
                          KEY idx_zeek_alerts_severity (severity),
                          KEY idx_zeek_alerts_src_ip (src_ip),
                          KEY idx_zeek_alerts_dest_ip (dest_ip),
                          KEY idx_zeek_alerts_processed_at (processed_at),
                          CONSTRAINT zeek_alerts_ibfk_1 FOREIGN KEY (institution_id) REFERENCES institutions (id)
                        )
                    """))
                    conn.commit()
                    print("Tabela zeek_alerts criada.")
            return
        # zeek_alerts existe com estrutura antiga
        conn.execute(text("RENAME TABLE zeek_alerts TO incidents"))
        conn.execute(text("""
            CREATE TABLE zeek_alerts (
              id int(11) NOT NULL AUTO_INCREMENT,
              institution_id int(11) NOT NULL,
              detected_at datetime NOT NULL,
              signature varchar(500) NOT NULL,
              signature_id varchar(50) DEFAULT NULL,
              severity enum('LOW','MEDIUM','HIGH','CRITICAL') NOT NULL DEFAULT 'MEDIUM',
              src_ip varchar(45) DEFAULT NULL,
              dest_ip varchar(45) DEFAULT NULL,
              src_port varchar(20) DEFAULT NULL,
              dest_port varchar(20) DEFAULT NULL,
              protocol varchar(20) DEFAULT NULL,
              category varchar(255) DEFAULT NULL,
              raw_log_data text DEFAULT NULL,
              processed_at datetime DEFAULT NULL,
              created_at datetime DEFAULT NULL,
              updated_at datetime DEFAULT NULL,
              PRIMARY KEY (id),
              KEY idx_zeek_alerts_institution_id (institution_id),
              KEY idx_zeek_alerts_detected_at (detected_at),
              KEY idx_zeek_alerts_severity (severity),
              KEY idx_zeek_alerts_src_ip (src_ip),
              KEY idx_zeek_alerts_dest_ip (dest_ip),
              KEY idx_zeek_alerts_processed_at (processed_at),
              CONSTRAINT zeek_alerts_ibfk_1 FOREIGN KEY (institution_id) REFERENCES institutions (id)
            )
        """))
        conn.commit()
        print("Migration executada: zeek_alerts -> incidents e nova tabela zeek_alerts criada.")


if __name__ == "__main__":
    main()
