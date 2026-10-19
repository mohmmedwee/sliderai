import { DataTable } from '../table/DataTable'
import type { SlideProps } from '../types'
import { TextBlock } from '../TextBlock'

export function Table({ slide, mode, selected, onSelect, onChange }: SlideProps) {
  const table = slide.table
  return (
    <div className="layout-table">
      <TextBlock path="title" text={slide.title} className="title-md" mode={mode} selected={selected} onSelect={onSelect} onChange={onChange} />
      {table ? <DataTable columns={table.columns} rows={table.rows} /> : null}
    </div>
  )
}
