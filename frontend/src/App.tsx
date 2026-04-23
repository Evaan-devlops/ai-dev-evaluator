import React, { useEffect } from 'react'
import { WorkbenchPage } from './features/workbench/WorkbenchPage'
import { useWorkbenchStore } from './store/workbenchStore'
import { useLLMConfigStore } from './store/llmConfigStore'

export default function App(): React.ReactElement {
  const loadDefaults = useWorkbenchStore((s) => s.loadDefaults)
  const dataSource = useLLMConfigStore((s) => s.config.dataSource)

  useEffect(() => {
    loadDefaults(dataSource)
  }, [dataSource, loadDefaults])

  return <WorkbenchPage />
}
