import { useEffect, useMemo, useRef, useState } from 'react'
import { Api } from './api'
import type { BackendInfo, Device, JobStatus, SpeakerStat } from './types'
import { Settings } from './Settings'

type Step = 'loading' | 'import' | 'configure' | 'run' | 'speakers' | 'export' | 'error'

export default function App() {
  const [api, setApi] = useState<Api | null>(null)
  const [step, setStep] = useState<Step>('loading')
  const [fatal, setFatal] = useState<string>('')
  const [showSettings, setShowSettings] = useState(false)

  // inputs
  const [mediaPath, setMediaPath] = useState('')
  const [transcriptPath, setTranscriptPath] = useState('')
  const [outputDir, setOutputDir] = useState('')

  // metadata
  const [devices, setDevices] = useState<Device[]>([])
  const [diarBackends, setDiarBackends] = useState<BackendInfo[]>([])
  const [asrBackends, setAsrBackends] = useState<BackendInfo[]>([])

  // config
  const [diar, setDiar] = useState('pyannote-local')
  const [asr, setAsr] = useState('faster-whisper-local')
  const [device, setDevice] = useState('auto')
  const [numSpeakers, setNumSpeakers] = useState('')
  const [language, setLanguage] = useState('')

  // job
  const [job, setJob] = useState<JobStatus | null>(null)
  const [log, setLog] = useState<string[]>([])
  const [initialSpeakers, setInitialSpeakers] = useState<SpeakerStat[]>([])
  const [names, setNames] = useState<Record<string, string>>({})
  const closeWs = useRef<() => void>()

  // --- boot: wait for backend, load metadata ---
  useEffect(() => {
    let cancelled = false
    const boot = async () => {
      try {
        const url = await window.diariza.backendUrl()
        const a = new Api(url || 'http://127.0.0.1:8765')
        // poll health until ready
        for (let i = 0; i < 150; i++) {
          try {
            await a.health()
            break
          } catch {
            await new Promise((r) => setTimeout(r, 400))
          }
          if (i === 149) throw new Error('backend not reachable')
        }
        if (cancelled) return
        const b = await a.backends()
        const devs = await a.devices()
        setApi(a)
        setDiarBackends(b.diarization)
        setAsrBackends(b.transcription)
        setDevices(devs)
        setStep('import')
      } catch (e) {
        setFatal(String(e))
        setStep('error')
      }
    }
    window.diariza.onBackendError((err) => {
      setFatal(err)
      setStep('error')
    })
    window.diariza.onLog((line) => setLog((l) => [...l.slice(-400), line]))
    boot()
    return () => {
      cancelled = true
    }
  }, [])

  const deviceLabel = useMemo(() => {
    const best = devices.find((d) => d.usable && d.kind !== 'cpu')
    return best ? `${best.kind.toUpperCase()} — ${best.name}` : 'CPU'
  }, [devices])

  const isModeA = !transcriptPath // ASR from scratch when no transcript imported

  async function pickMedia() {
    const p = await window.diariza.openFile([
      { name: 'Media', extensions: ['mp4', 'mkv', 'mov', 'avi', 'wav', 'mp3', 'm4a', 'flac'] }
    ])
    if (p) setMediaPath(p)
  }
  async function pickTranscript() {
    const p = await window.diariza.openFile([{ name: 'Transcript', extensions: ['vtt', 'srt'] }])
    if (p) setTranscriptPath(p)
  }
  async function pickOut() {
    const p = await window.diariza.openDir()
    if (p) setOutputDir(p)
  }

  async function start() {
    if (!api) return
    setLog([])
    setJob(null)
    const req = {
      media_path: mediaPath,
      transcript_path: transcriptPath || null,
      diarization_backend: diar,
      transcription_backend: asr,
      num_speakers: numSpeakers ? Number(numSpeakers) : null,
      language: language || null,
      device,
      output_dir: outputDir || 'out'
    }
    try {
      const created = await api.createJob(req)
      setJob(created)
      setStep('run')
      closeWs.current?.()
      closeWs.current = api.events(created.id, (e) => {
        if (e.type === 'progress') {
          setJob((j) => (j ? { ...j, progress: Number(e.progress), message: String(e.message) } : j))
        } else if (e.type === 'done') {
          api.getJob(created.id).then((full) => {
            setJob(full)
            setInitialSpeakers(full.speakers ?? [])
            setStep('speakers')
          })
        } else if (e.type === 'error') {
          setJob((j) => (j ? { ...j, status: 'error', error: String(e.error) } : j))
        } else if (e.type === 'cancelled') {
          setJob((j) => (j ? { ...j, status: 'cancelled' } : j))
        }
      })
    } catch (e) {
      setFatal(String(e))
      setStep('error')
    }
  }

  async function cancel() {
    if (api && job) await api.cancelJob(job.id)
  }

  async function applyNames() {
    if (!api || !job) return
    const updated = await api.relabel(job.id, names)
    setJob(updated)
  }

  // ---------- render ----------
  if (step === 'loading')
    return <Center>Starting the diariza engine…</Center>
  if (step === 'error')
    return (
      <Center>
        <h2>Backend error</h2>
        <pre className="error">{fatal}</pre>
        <p className="muted">Check that Python and the engine are installed (dev), or reinstall the app.</p>
      </Center>
    )

  return (
    <div className="app">
      <header>
        <div className="brand">diariza</div>
        <nav>
          <Stepper step={step} />
          <button className="ghost" onClick={() => setShowSettings(true)}>Settings</button>
        </nav>
      </header>

      <main>
        {step === 'import' && (
          <section>
            <h2>1 · Import</h2>
            <Field label="Media file (video or audio)" required>
              <PathInput value={mediaPath} onPick={pickMedia} placeholder="Choose a video/audio file…" />
            </Field>
            <Field label="Existing transcript (optional — VTT/SRT)">
              <PathInput value={transcriptPath} onPick={pickTranscript} placeholder="Leave empty to transcribe with Whisper" onClear={() => setTranscriptPath('')} />
            </Field>
            <p className="muted">
              {isModeA ? 'Mode A: transcribe from scratch, then diarize.' : 'Mode B: add speakers to your transcript.'}
            </p>
            <div className="actions">
              <button disabled={!mediaPath} onClick={() => setStep('configure')}>Next</button>
            </div>
          </section>
        )}

        {step === 'configure' && (
          <section>
            <h2>2 · Configure</h2>
            <div className="grid">
              <Field label="Diarization model">
                <select value={diar} onChange={(e) => setDiar(e.target.value)}>
                  {diarBackends.map((b) => (
                    <option key={b.name} value={b.name}>{b.name}</option>
                  ))}
                </select>
              </Field>
              {isModeA && (
                <Field label="Transcription model">
                  <select value={asr} onChange={(e) => setAsr(e.target.value)}>
                    {asrBackends.map((b) => (
                      <option key={b.name} value={b.name}>{b.name}</option>
                    ))}
                  </select>
                </Field>
              )}
              <Field label="Device">
                <select value={device} onChange={(e) => setDevice(e.target.value)}>
                  <option value="auto">Auto (detected: {deviceLabel})</option>
                  <option value="gpu">GPU</option>
                  <option value="cpu">CPU</option>
                </select>
              </Field>
              <Field label="Number of speakers (blank = auto)">
                <input type="number" min={1} value={numSpeakers} onChange={(e) => setNumSpeakers(e.target.value)} />
              </Field>
              {isModeA && (
                <Field label="Language (blank = auto-detect)">
                  <input value={language} onChange={(e) => setLanguage(e.target.value)} placeholder="e.g. hu, en" />
                </Field>
              )}
              <Field label="Output folder">
                <PathInput value={outputDir} onPick={pickOut} placeholder="Default: ./out" />
              </Field>
            </div>
            <div className="actions">
              <button className="ghost" onClick={() => setStep('import')}>Back</button>
              <button onClick={start}>Start</button>
            </div>
          </section>
        )}

        {step === 'run' && job && (
          <section>
            <h2>3 · Run</h2>
            <div className="progress"><div style={{ width: `${Math.round(job.progress * 100)}%` }} /></div>
            <p>{Math.round(job.progress * 100)}% — {job.message}</p>
            {job.status === 'error' && <pre className="error">{job.error}</pre>}
            <pre className="log">{log.slice(-120).join('')}</pre>
            <div className="actions">
              <button className="ghost" onClick={cancel}>Cancel</button>
            </div>
          </section>
        )}

        {step === 'speakers' && job && (
          <section>
            <h2>4 · Speakers</h2>
            <p className="muted">Rename speakers. Give two rows the same name to merge them, then Apply.</p>
            <table className="speakers">
              <thead><tr><th>Detected</th><th>Speaking time</th><th>Lines</th><th>Name</th></tr></thead>
              <tbody>
                {initialSpeakers.map((s) => (
                  <tr key={s.speaker}>
                    <td><code>{s.speaker}</code></td>
                    <td>{s.minutes} min</td>
                    <td>{s.cues}</td>
                    <td>
                      <input
                        value={names[s.speaker] ?? ''}
                        placeholder={s.speaker}
                        onChange={(e) => setNames({ ...names, [s.speaker]: e.target.value })}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="actions">
              <button className="ghost" onClick={applyNames}>Apply names</button>
              <button onClick={() => setStep('export')}>Next</button>
            </div>
          </section>
        )}

        {step === 'export' && job && (
          <section>
            <h2>5 · Export</h2>
            <p>Done. Files written:</p>
            <ul className="outputs">
              {Object.entries(job.outputs ?? {}).map(([k, v]) => (
                <li key={k}>
                  <span className="kind">{k}</span>
                  <code>{v}</code>
                  <button className="ghost sm" onClick={() => window.diariza.showInFolder(v)}>Reveal</button>
                </li>
              ))}
            </ul>
            <div className="actions">
              <button className="ghost" onClick={() => setStep('import')}>New job</button>
            </div>
          </section>
        )}
      </main>

      {showSettings && api && <Settings api={api} onClose={() => setShowSettings(false)} />}
    </div>
  )
}

// ---------- small presentational helpers ----------
function Center({ children }: { children: React.ReactNode }) {
  return <div className="center">{children}</div>
}

function Stepper({ step }: { step: Step }) {
  const steps: Step[] = ['import', 'configure', 'run', 'speakers', 'export']
  return (
    <ol className="stepper">
      {steps.map((s, i) => (
        <li key={s} className={s === step ? 'on' : ''}>{i + 1}. {s}</li>
      ))}
    </ol>
  )
}

function Field({ label, required, children }: { label: string; required?: boolean; children: React.ReactNode }) {
  return (
    <label className="field">
      <span>{label}{required && <em> *</em>}</span>
      {children}
    </label>
  )
}

function PathInput({ value, onPick, onClear, placeholder }: { value: string; onPick: () => void; onClear?: () => void; placeholder?: string }) {
  return (
    <div className="pathinput">
      <input readOnly value={value} placeholder={placeholder} />
      <button className="ghost" onClick={onPick}>Browse</button>
      {onClear && value && <button className="ghost" onClick={onClear}>✕</button>}
    </div>
  )
}
