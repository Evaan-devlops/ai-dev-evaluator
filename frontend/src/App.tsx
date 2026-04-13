import React, { useEffect } from 'react'
import { WorkbenchPage } from './features/workbench/WorkbenchPage'
import { useWorkbenchStore } from './store/workbenchStore'

export default function App(): React.ReactElement {
  const loadDefaults = useWorkbenchStore((s) => s.loadDefaults)

  useEffect(() => {
    loadDefaults()
  }, [loadDefaults])

  return <WorkbenchPage />
}
