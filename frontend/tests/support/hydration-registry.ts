import { z } from 'zod'
import type { HydrationRegistry } from '@tinyteamco/hydration-test-utils'
import {
  userIdAtom,
  userEmailAtom,
  userOrgIdAtom,
  userOrganizationNameAtom,
  userRoleAtom,
  userFirebaseUidAtom,
} from '../../src/atoms/auth'
import { organizationsAtom } from '../../src/atoms/organizations'

// Schemas
const userSchema = z.object({
  id: z.number(),
  email: z.string().email(),
  orgId: z.number().nullable(),
  organizationName: z.string().nullable(),
  role: z.enum(['owner', 'admin', 'member', 'super_admin']),
  firebaseUid: z.string(),
})

const organizationSchema = z.object({
  org_id: z.string(),
  name: z.string(),
  created_at: z.string(),
})

// Hydration registry
export const hydrationRegistry: HydrationRegistry = {
  user: {
    schema: userSchema,
    atoms: {
      id: userIdAtom,
      email: userEmailAtom,
      orgId: userOrgIdAtom,
      organizationName: userOrganizationNameAtom,
      role: userRoleAtom,
      firebaseUid: userFirebaseUidAtom,
    },
  },
  // For organizations array, use object-storing pattern
  organizations: {
    schema: z.array(organizationSchema),
    atoms: {
      organizations: organizationsAtom, // Atom name matches section name
    },
  },
}

// Export types
export type User = z.infer<typeof userSchema>
export type Organization = z.infer<typeof organizationSchema>
