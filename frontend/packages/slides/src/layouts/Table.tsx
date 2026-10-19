import type { SlideProps } from '../types'
import { TextBlock } from '../TextBlock'

export function Table({ slide, mode, selected, onSelect, onChange }: SlideProps) {
  const table = slide.table
  return (
    <div className="layout-table">
      <TextBlock path="title" text={slide.title} className="title-md" mode={mode} selected={selected} onSelect={onSelect} onChange={onChange} />
      {table ? (
        <table className="data-table">
          <thead>
            <tr>
              {table.columns.map((column) => (
                <th key={column} title={column}>
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {table.rows.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {row.map((cell, cellIndex) => (
                  <td key={cellIndex} title={cell == null ? '' : String(cell)} className={typeof cell === 'number' ? 'num' : undefined}>
                    {cell == null ? '' : String(cell)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
    </div>
  )
}
