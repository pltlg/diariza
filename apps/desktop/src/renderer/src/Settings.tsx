import { useEffect, useState } from 'react'
import type { Api } from './api'

/** Secrets are write-only from the UI (stored in the OS keychain by the backend, never read back). */
const SECRETS = [
  { key: 'HF_TOKEN', label: 'Hugging Face token (for gated pyannote models)' },
  { key: 'PYANNOTEAI_API_KEY', label: 'pyannoteAI API key (cloud)' },
  { key: 'ASSEMBLYAI_API_KEY', label: 'AssemblyAI API key (cloud)' },
  { key: 'DEEPGRAM_API_KEY', label: 'Deepgram API key (cloud)' }
]

export function Settings({ api, onClose }: { api: Api; onClose: () => void }) {
  const [values, setValues] = useState<Record<string, string>>({})
  const [saved, setSaved] = useState('')
  const [version, setVersion] = useState('')

  useEffect(() => {
    api.health().then((h) => setVersion(h.version)).catch(() => undefined)
  }, [api])

  async function save(key: string) {
    const v = values[key]
    if (!v) return
    await api.setSecret(key, v)
    setValues({ ...values, [key]: '' })
    setSaved(`${key} saved`)
    setTimeout(() => setSaved(''), 2000)
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>Settings</h2>
        <p className="muted">
          Accept the gated models at hf.co/pyannote/speaker-diarization-3.1 and segmentation-3.0
          with the account that owns your token.
        </p>
        {SECRETS.map((s) => (
          <label className="field" key={s.key}>
            <span>{s.label}</span>
            <div className="pathinput">
              <input
                type="password"
                value={values[s.key] ?? ''}
                placeholder="••••••••"
                onChange={(e) => setValues({ ...values, [s.key]: e.target.value })}
              />
              <button className="ghost" onClick={() => save(s.key)}>Save</button>
            </div>
          </label>
        ))}
        {saved && <p className="ok">{saved}</p>}
        <div className="actions">
          <span className="muted">engine v{version}</span>
          <button onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  )
}
