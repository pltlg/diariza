import type { DiarizaApi } from '../../preload'

declare global {
  interface Window {
    diariza: DiarizaApi
  }
}

export {}
