import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'

const API = 'http://127.0.0.1:8000'

type StatusRow = {
  sheet_row: number
  data: Record<string, string>
}

function LarkJobSheetPage() {
  const [rows, setRows] = useState<StatusRow[]>([])
  const [loading, setLoading] = useState(true)
  const [busyRow, setBusyRow] = useState<number | null>(null)

  useEffect(() => {
    setLoading(true)
    fetch(`${API}/project-status-rows`)
      .then((r) => r.json())
      .then((body) => {
        if (body.status !== 'success') {
          toast.error(body.error || 'Could not load sheet rows.')
          setRows([])
          return
        }
        setRows(body.rows ?? [])
      })
      .catch(() => {
        toast.error('Could not reach backend.')
        setRows([])
      })
      .finally(() => setLoading(false))
  }, [])

  const generate = (item: StatusRow) => {
    setBusyRow(item.sheet_row)
    fetch(`${API}/generate-lark-job-sheet`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ row: item.data }),
    })
      .then((r) => r.json())
      .then((body) => {
        if (body.status !== 'success') {
          toast.error(body.error || 'Generation failed.')
          return
        }
        const url = `https://larksuite.com/docx/${body.document_id}`
        toast.success(
          <span>
            Job sheet created.{' '}
            <a href={url} target="_blank" rel="noreferrer" className="font-semibold underline">
              Open
            </a>
          </span>,
          { duration: 5000 },
        )
      })
      .catch(() => toast.error('Request failed.'))
      .finally(() => setBusyRow(null))
  }

  return (
    <div className="min-h-screen bg-slate-50 p-6 text-slate-900">
      <div className="mx-auto max-w-3xl">
        <div className="mb-6 rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
          <h1 className="text-2xl font-semibold tracking-tight">Project status → Lark job sheet</h1>
          <p className="mt-2 text-sm text-slate-600">
            Rows from your Lark spreadsheet. Generate opens a new Doc in the configured NSW folder.
          </p>
        </div>

        <section className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold">Rows</h2>
            <span className="text-xs text-slate-500">{rows.length} loaded</span>
          </div>

          {loading ? (
            <div className="flex flex-col items-center justify-center gap-3 py-16 text-sm text-slate-500">
              <div
                className="h-8 w-8 animate-spin rounded-full border-2 border-slate-300 border-t-slate-700"
                aria-hidden
              />
              <span>Loading…</span>
            </div>
          ) : rows.length === 0 ? (
            <p className="py-8 text-center text-sm text-slate-500">No data rows found.</p>
          ) : (
            <ul className="max-h-[min(70vh,640px)] space-y-3 overflow-y-auto pr-1">
              {rows.map((item) => {
                const name = item.data['Customer Name'] ?? '—'
                const addr = item.data['Project Address'] ?? '—'
                return (
                  <li
                    key={item.sheet_row}
                    className="flex flex-col gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4 sm:flex-row sm:items-center sm:justify-between"
                  >
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium text-slate-900">{name}</p>
                      <p className="mt-1 line-clamp-2 text-xs text-slate-600">{addr}</p>
                      <p className="mt-1 text-xs text-slate-400">Sheet row {item.sheet_row}</p>
                    </div>
                    <button
                      type="button"
                      onClick={() => generate(item)}
                      disabled={busyRow === item.sheet_row}
                      className="inline-flex shrink-0 items-center justify-center gap-2 rounded-lg bg-black px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      {busyRow === item.sheet_row ? (
                        <>
                          <span
                            className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white"
                            aria-hidden
                          />
                          <span>Generating…</span>
                        </>
                      ) : (
                        'Generate job sheet'
                      )}
                    </button>
                  </li>
                )
              })}
            </ul>
          )}
        </section>
      </div>
    </div>
  )
}

export default LarkJobSheetPage
