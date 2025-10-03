import { atom } from 'jotai'

export interface Organization {
  org_id: string
  name: string
  created_at: string
}

// Organizations atom (array data)
export const organizationsAtom = atom<Organization[]>([])
