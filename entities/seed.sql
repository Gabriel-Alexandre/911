-- Criar tipos ENUM para a tabela emergency
CREATE TYPE emergency_level AS ENUM ('CRÍTICO', 'ALTO', 'MÉDIO', 'BAIXO');
CREATE TYPE emergency_status AS ENUM ('ATIVO', 'EM_ANDAMENTO', 'RESOLVIDO', 'FINALIZADO');

-- Tabela emergency
CREATE TABLE IF NOT EXISTS emergency (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    level emergency_level NOT NULL,
    status emergency_status NOT NULL DEFAULT 'ATIVO',
    responsible VARCHAR(255) NOT NULL,
    location VARCHAR(255) NOT NULL,
    victim VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    reporter VARCHAR(255) NOT NULL
);

-- Tabela ticket (baseada na interface BackendEmergency)
CREATE TABLE IF NOT EXISTS ticket (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    success BOOLEAN NOT NULL DEFAULT true,
    emergency_type TEXT[] NOT NULL,
    urgency_level INTEGER NOT NULL CHECK (urgency_level >= 1 AND urgency_level <= 5),
    situation TEXT NOT NULL,
    confidence_score DECIMAL(3,2) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    location VARCHAR(255),
    victim VARCHAR(255),
    reporter VARCHAR(255),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índices para melhorar performance
CREATE INDEX IF NOT EXISTS idx_emergency_status ON emergency(status);
CREATE INDEX IF NOT EXISTS idx_emergency_level ON emergency(level);
CREATE INDEX IF NOT EXISTS idx_emergency_created_at ON emergency(created_at);
CREATE INDEX IF NOT EXISTS idx_emergency_location ON emergency(location);

CREATE INDEX IF NOT EXISTS idx_ticket_urgency_level ON ticket(urgency_level);
CREATE INDEX IF NOT EXISTS idx_ticket_timestamp ON ticket(timestamp);
CREATE INDEX IF NOT EXISTS idx_ticket_emergency_type ON ticket USING GIN(emergency_type);

-- Trigger para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_emergency_updated_at 
    BEFORE UPDATE ON emergency 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ticket_updated_at 
    BEFORE UPDATE ON ticket 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
