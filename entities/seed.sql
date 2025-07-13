-- Tabela ocorrencias (substitui emergency e ticket)
CREATE TABLE IF NOT EXISTS ocorrencias (
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
CREATE INDEX IF NOT EXISTS idx_ocorrencias_urgency_level ON ocorrencias(urgency_level);
CREATE INDEX IF NOT EXISTS idx_ocorrencias_timestamp ON ocorrencias(timestamp);
CREATE INDEX IF NOT EXISTS idx_ocorrencias_emergency_type ON ocorrencias USING GIN(emergency_type);
CREATE INDEX IF NOT EXISTS idx_ocorrencias_location ON ocorrencias(location);
CREATE INDEX IF NOT EXISTS idx_ocorrencias_created_at ON ocorrencias(created_at);

-- Trigger para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_ocorrencias_updated_at 
    BEFORE UPDATE ON ocorrencias 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
