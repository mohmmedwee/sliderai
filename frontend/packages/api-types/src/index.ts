export type { components, paths } from './schema'

import type { components, paths } from './schema'

export type Schemas = components['schemas']
export type TurnEvent =
  paths['/v1/_schema/turn-event']['get']['responses'][200]['content']['application/json']
