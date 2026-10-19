export function DataTable({
  columns,
  rows,
}: {
  columns: string[]
  rows: (string | number | null)[][]
}) {
  const head = columns.slice(0, 8)
  const body = rows.slice(0, 12)
  return (
    <table className="data-table">
      <thead>
        <tr>
          {head.map((column) => (
            <th key={column} title={column}>
              {column}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {body.map((row, rowIndex) => (
          <tr key={rowIndex}>
            {head.map((_, cellIndex) => {
              const cell = row[cellIndex]
              const text = cell == null ? '' : String(cell)
              const numeric = typeof cell === 'number' && Number.isFinite(cell)
              return (
                <td key={cellIndex} title={text} className={numeric ? 'num' : undefined}>
                  {text}
                </td>
              )
            })}
          </tr>
        ))}
      </tbody>
    </table>
  )
}
