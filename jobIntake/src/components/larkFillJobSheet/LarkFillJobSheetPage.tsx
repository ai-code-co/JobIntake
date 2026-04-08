import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'

type FileType = {
  name: string
  url: string
  token: string
}

type SheetData = Record<string, string>

function LarkFillJobSheetPage() {
  const [allFiles, setAllFiles] = useState<FileType[]>([])
  const [extractedData, setExtractedData] = useState<SheetData>({})
  const [selectedFile, setSelectedFile] = useState<FileType | null>(null)
  const [loadingFiles, setLoadingFiles] = useState(true)
  const [extractingToken, setExtractingToken] = useState<string | null>(null)
  const [isFilling, setIsFilling] = useState(false)
  const [editingKey, setEditingKey] = useState<string | null>(null)
  const valueCellRefs = useRef<Map<string, HTMLDivElement | null>>(new Map())

  const setValueCellRef = useCallback((key: string) => (el: HTMLDivElement | null) => {
    if (el) {
      valueCellRefs.current.set(key, el)
    } else {
      valueCellRefs.current.delete(key)
    }
  }, [])

  useEffect(() => {
    if (editingKey === null) return
    const onPointerDown = (e: PointerEvent) => {
      const cell = valueCellRefs.current.get(editingKey)
      const target = e.target as Node
      if (cell && !cell.contains(target)) {
        setEditingKey(null)
      }
    }
    document.addEventListener('pointerdown', onPointerDown)
    return () => document.removeEventListener('pointerdown', onPointerDown)
  }, [editingKey])

  useEffect(() => {
    setLoadingFiles(true)
    fetch("http://127.0.0.1:8000/list-all-lark-docs")
      .then(response => response.json())
      .then(data => setAllFiles(data?.data ?? []))
      .catch(error => {
        console.error('Error:', error)
        toast.error('Could not load Lark docs. Please check backend and try again.')
      })
      .finally(() => setLoadingFiles(false))
  }, [])

  const extractLarkDoc = (token: string) => {
    setExtractedData({})
    setEditingKey(null)
    setExtractingToken(token)
    fetch(`http://127.0.0.1:8000/extract-lark-doc/${token}`)
      .then(response => response.json())
      .then(data => {
        setExtractedData(data?.sheet_data ?? {})
        setEditingKey(null)
        toast.success('Data extracted successfully.')
      })
      .catch(error => {
        console.error('Error:', error)
        toast.error('Extraction failed. Please try again.')
      })
      .finally(() => setExtractingToken(null))
  }

  const fillLarkSheet = (data: SheetData) => {
    setIsFilling(true)
    fetch(`http://127.0.0.1:8000/fill-lark-sheet`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(data)
    })
      .then(response => response.json())
      .then(data => {
        console.log("data ", data)
        if (data?.status === 'success') {
          toast.success('Row appended to Lark sheet.')
        } else {
          toast.error('Fill failed. Check backend response.')
        }
      })
      .catch(error => {
        console.error('Error:', error)
        toast.error('Fill request failed. Please try again.')
      })
      .finally(() => setIsFilling(false))
  }

  const extractedEntries = Object.entries(extractedData)

  return (
    <div className="min-h-screen bg-slate-50 p-6 text-slate-900">
      <div className="mx-auto max-w-7xl">
        <div className="mb-6 rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
          <h1 className="text-2xl font-semibold tracking-tight">Lark Job Sheet Extractor</h1>
          <p className="mt-2 text-sm text-slate-600">
            Select a Lark doc, extract fields, review as a table, then append to your spreadsheet.
          </p>
          <Link
            to="/jobsheet"
            className="mt-3 inline-block text-sm font-medium text-emerald-700 hover:text-emerald-800 hover:underline"
          >
            Project status → generate job sheets
          </Link>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <section className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold">Available Lark Docs</h2>
              <span className="text-xs text-slate-500">{allFiles.length} docs</span>
            </div>

            {loadingFiles ? (
              <div className="rounded-xl border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500">
                <div className="mx-auto h-6 w-6 animate-spin rounded-full border-2 border-slate-300 border-t-slate-700" />
                <p className="mt-2">Loading files...</p>
              </div>
            ) : allFiles.length > 0 ? (
              <div className="space-y-3 overflow-y-scroll max-h-[540px]">
                {allFiles.map((file) => (
                  <div
                    key={file.token}
                    className={`rounded-xl border p-4 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md hover:ring-1 hover:ring-slate-300 ${
                      selectedFile?.token === file.token
                        ? 'border-slate-400 bg-slate-100'
                        : 'border-slate-200 bg-slate-50'
                    }`}
                  >
                    <h3 className="line-clamp-2 text-sm font-medium">{file.name}</h3>
                    <a
                      href={file.url}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-1 block truncate text-xs text-green-700 hover:text-green-800 hover:underline"
                    >
                      {file.url}
                    </a>
                    <div className="mt-3">
                      <button
                        onClick={() => {
                          setSelectedFile(file)
                          extractLarkDoc(file.token)
                        }}
                        disabled={extractingToken === file.token}
                        className="rounded-lg bg-black px-3 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        {extractingToken === file.token ? 'Extracting...' : 'Extract Data'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="rounded-xl border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500">
                No docs found in Lark root folders.
              </div>
            )}
          </section>

          <section className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold">Extracted Sheet Data</h2>
                <p className="text-xs text-slate-500">
                  {selectedFile ? `Source: ${selectedFile.name}` : 'No file selected yet'}
                </p>
              </div>
              <button
                onClick={() => fillLarkSheet(extractedData)}
                disabled={extractedEntries.length === 0 || isFilling}
                className="rounded-lg bg-emerald-600 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isFilling ? 'Filling...' : 'Fill Lark Sheet'}
              </button>
            </div>

            {extractedEntries.length > 0 ? (
              <div className="max-h-[540px] overflow-auto rounded-xl border border-slate-200">
                <table className="min-w-full text-sm">
                  <thead className="sticky top-0 bg-slate-100">
                    <tr>
                      <th className="w-1/3 border-b border-slate-200 px-4 py-3 text-left font-semibold text-slate-700">
                        Field
                      </th>
                      <th className="border-b border-slate-200 px-4 py-3 text-left font-semibold text-slate-700">
                        Value
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {extractedEntries.map(([key, value]) => {
                      const isEditing = editingKey === key
                      const display = value?.trim() ? value : null
                      return (
                        <tr key={key} className="odd:bg-white even:bg-slate-50">
                          <td className="border-b border-slate-100 px-4 py-2 font-medium text-slate-700">{key}</td>
                          <td className="border-b border-slate-100 px-4 py-2 text-slate-600">
                            <div
                              ref={setValueCellRef(key)}
                              className="min-h-[2rem] cursor-text rounded px-1 py-0.5 hover:bg-slate-100/80"
                              role="button"
                              tabIndex={0}
                              onKeyDown={(e) => {
                                if (isEditing) return
                                if (e.key === 'Enter' || e.key === ' ') {
                                  e.preventDefault()
                                  setEditingKey(key)
                                }
                              }}
                              onClick={() => setEditingKey(key)}
                            >
                              {isEditing ? (
                                <input
                                  type="text"
                                  className="w-full rounded border border-slate-300 bg-white px-2 py-1 text-slate-800 outline-none ring-blue-500 focus:ring-2"
                                  value={value}
                                  placeholder="-"
                                  autoFocus
                                  onChange={(e) =>
                                    setExtractedData((prev) => ({ ...prev, [key]: e.target.value }))
                                  }
                                  onClick={(e) => e.stopPropagation()}
                                />
                              ) : display ? (
                                <span>{display}</span>
                              ) : (
                                <span className="text-slate-400">-</span>
                              )}
                            </div>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            ) : extractingToken ? (
              <div className="rounded-xl border border-dashed border-slate-300 p-10 text-center text-sm text-slate-500">
                <div className="mx-auto h-6 w-6 animate-spin rounded-full border-2 border-slate-300 border-t-slate-700" />
                <p className="mt-2">Extracting sheet data...</p>
              </div>
            ) : (
              <div className="rounded-xl border border-dashed border-slate-300 p-10 text-center text-sm text-slate-500">
                Extract a file to preview data in table format.
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  )
}

export default LarkFillJobSheetPage