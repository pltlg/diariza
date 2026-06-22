export interface Device {
  kind: 'cuda' | 'mps' | 'cpu'
  name: string
  usable: boolean
  detail: string
}

export interface BackendInfo {
  name: string
  requires_api_key?: boolean
  supports_num_speakers?: boolean
  config_schema?: Record<string, unknown>
  available?: boolean
  error?: string
}

export interface SpeakerStat {
  speaker: string
  minutes: number
  cues: number
  samples: number[]
}

export interface JobStatus {
  id: string
  status: 'queued' | 'running' | 'done' | 'error' | 'cancelled'
  progress: number
  message: string
  error?: string | null
  speakers?: SpeakerStat[]
  outputs?: Record<string, string>
}

export interface JobRequest {
  media_path: string
  transcript_path?: string | null
  diarization_backend: string
  transcription_backend: string
  num_speakers?: number | null
  language?: string | null
  device: string
  output_dir: string
}
