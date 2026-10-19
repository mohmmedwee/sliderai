import type { Slide } from '../src/types'

export const en: Record<Slide['layout'], Slide> = {
  hero: {
    id: 'enhero0001',
    layout: 'hero',
    kicker: 'Launch',
    title: 'A clear story',
    body: 'One idea, said plainly.',
    button: 'Start',
    field: '#aabbcc',
  },
  title: {
    id: 'entitle001',
    layout: 'title',
    kicker: 'Quarter',
    title: 'The year so far',
    body: 'What changed, and what is next.',
  },
  points: {
    id: 'enpoints01',
    layout: 'points',
    title: 'Three points',
    points: ['First', 'Second'],
  },
  quote: {
    id: 'enquote001',
    layout: 'quote',
    title: 'Make it obvious.',
    body: 'Ada',
  },
  split: {
    id: 'ensplit001',
    layout: 'split',
    kicker: 'Side',
    title: 'Text and field',
    body: 'The field sits at the end.',
    button: 'Next',
    field: '#112233',
  },
  table: {
    id: 'entable001',
    layout: 'table',
    title: 'Numbers',
    table: { columns: ['Name', 'Count'], rows: [['Alpha', 2]] },
  },
  chart: {
    id: 'enchart001',
    layout: 'chart',
    title: 'Growth',
    chart: { kind: 'bar', labels: ['Q1'], series: [{ name: 'Rev', values: [1] }] },
  },
}

export const ar: Record<Slide['layout'], Slide> = {
  hero: {
    id: 'arhero0001',
    layout: 'hero',
    kicker: 'إطلاق',
    title: 'قصة واضحة',
    body: 'فكرة واحدة، بجملة بسيطة.',
    button: 'ابدأ',
    field: '#aabbcc',
  },
  title: {
    id: 'artitle001',
    layout: 'title',
    kicker: 'الربع',
    title: 'السنة حتى الآن',
    body: 'ما تغيّر، وما يأتي بعد ذلك.',
  },
  points: {
    id: 'arpoints01',
    layout: 'points',
    title: 'ثلاث نقاط',
    points: ['الأولى', 'الثانية'],
  },
  quote: {
    id: 'arquote001',
    layout: 'quote',
    title: 'اجعلها واضحة.',
    body: 'هدى',
  },
  split: {
    id: 'arsplit001',
    layout: 'split',
    kicker: 'جانب',
    title: 'نص ومساحة',
    body: 'المساحة في الطرف.',
    button: 'التالي',
  },
  table: {
    id: 'artable001',
    layout: 'table',
    title: 'أرقام',
    table: { columns: ['الاسم', 'العدد'], rows: [['ألف', 2]] },
  },
  chart: {
    id: 'archart001',
    layout: 'chart',
    title: 'النمو',
    chart: { kind: 'line', labels: ['ر1'], series: [{ name: 'دخل', values: [1] }] },
  },
}
