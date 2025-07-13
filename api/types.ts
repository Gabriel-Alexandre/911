/**
 * Interface para representar uma ocorrência
 */
export interface Ocorrencia {
  success: boolean;
  emergency_type: string[]; // Ex: ["policia", "samu"]
  urgency_level: number;    // Ex: 1 a 5
  situation: string;
  confidence_score: number; // 0 a 1
  location?: string | null;
  victim?: string | null;
  reporter?: string | null;
  timestamp?: string; // ISO string
  id?: string;
  createdAt?: string;
  updatedAt?: string;
}

/**
 * Interface para filtros de busca de ocorrências
 */
export interface OcorrenciaFilters {
  urgency_level?: number;
  emergency_type?: string;
  location?: string;
  success?: boolean;
}

/**
 * Interface para resposta da listagem de ocorrências
 */
export interface OcorrenciasResponse {
  ocorrencias: Ocorrencia[];
  total: number;
}

/**
 * Interface para classificação de emergência
 */
export interface EmergencyClassification {
  relato: string;
  emergency_classification: string[];
  nivel_urgencia: number;
  status: string;
  timestamp: string;
} 
