export type Lang = 'en' | 'hu'

type Dict = Record<string, string>

const en: Dict = {
  starting: 'Starting the diariza engine…',
  backendError: 'Backend error',
  backendHint: 'Check that Python and the engine are installed (dev), or reinstall the app.',
  settings: 'Settings',
  // steps
  'step.import': 'Import',
  'step.configure': 'Configure',
  'step.run': 'Run',
  'step.speakers': 'Speakers',
  'step.export': 'Export',
  // import
  mediaFile: 'Media file (video or audio)',
  chooseMedia: 'Choose a video/audio file…',
  existingTranscript: 'Existing transcript (optional — VTT/SRT)',
  transcriptPlaceholder: 'Leave empty to transcribe with Whisper',
  modeA: 'Mode A: transcribe from scratch, then diarize.',
  modeB: 'Mode B: add speakers to your transcript.',
  // configure
  diarizationModel: 'Diarization model',
  transcriptionModel: 'Transcription model',
  device: 'Device',
  autoDetected: 'Auto (detected: {dev})',
  numSpeakers: 'Number of speakers (blank = auto)',
  language: 'Language (blank = auto-detect)',
  outputFolder: 'Output folder',
  outputDefault: 'Default: ./out',
  // run
  cancel: 'Cancel',
  // speakers
  speakersHint: 'Rename speakers. Give two rows the same name to merge them, then Apply.',
  detected: 'Detected',
  speakingTime: 'Speaking time',
  lines: 'Lines',
  name: 'Name',
  applyNames: 'Apply names',
  // export
  done: 'Done. Files written:',
  reveal: 'Reveal',
  newJob: 'New job',
  // buttons
  next: 'Next',
  back: 'Back',
  start: 'Start',
  browse: 'Browse',
  minutes: 'min'
}

const hu: Dict = {
  starting: 'A diariza motor indítása…',
  backendError: 'Háttérhiba',
  backendHint: 'Ellenőrizd, hogy a Python és a motor telepítve van (fejlesztői mód), vagy telepítsd újra az appot.',
  settings: 'Beállítások',
  'step.import': 'Import',
  'step.configure': 'Beállítás',
  'step.run': 'Futtatás',
  'step.speakers': 'Beszélők',
  'step.export': 'Exportálás',
  mediaFile: 'Médiafájl (videó vagy hang)',
  chooseMedia: 'Válassz videó-/hangfájlt…',
  existingTranscript: 'Meglévő átirat (opcionális — VTT/SRT)',
  transcriptPlaceholder: 'Hagyd üresen a Whisper-átirathoz',
  modeA: 'A mód: átirat a semmiből, majd diarizáció.',
  modeB: 'B mód: beszélők hozzáadása a meglévő átirathoz.',
  diarizationModel: 'Diarizációs modell',
  transcriptionModel: 'Átírási modell',
  device: 'Eszköz',
  autoDetected: 'Automatikus (észlelt: {dev})',
  numSpeakers: 'Beszélők száma (üres = automatikus)',
  language: 'Nyelv (üres = automatikus felismerés)',
  outputFolder: 'Kimeneti mappa',
  outputDefault: 'Alapértelmezett: ./out',
  cancel: 'Mégse',
  speakersHint: 'Nevezd át a beszélőket. Két sorhoz ugyanazt a nevet adva összevonod őket, majd Alkalmaz.',
  detected: 'Észlelt',
  speakingTime: 'Beszédidő',
  lines: 'Sorok',
  name: 'Név',
  applyNames: 'Nevek alkalmazása',
  done: 'Kész. Létrejött fájlok:',
  reveal: 'Megnyitás',
  newJob: 'Új feladat',
  next: 'Tovább',
  back: 'Vissza',
  start: 'Indítás',
  browse: 'Tallózás',
  minutes: 'perc'
}

const dicts: Record<Lang, Dict> = { en, hu }

export function makeT(lang: Lang) {
  return (key: string, vars?: Record<string, string>): string => {
    let s = dicts[lang][key] ?? en[key] ?? key
    if (vars) for (const k of Object.keys(vars)) s = s.replace(`{${k}}`, vars[k])
    return s
  }
}

export function loadLang(): Lang {
  return (localStorage.getItem('diariza.lang') as Lang) || 'en'
}
export function saveLang(l: Lang): void {
  localStorage.setItem('diariza.lang', l)
}
