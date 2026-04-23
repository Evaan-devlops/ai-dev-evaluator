import React from 'react'
import styles from './WorkbenchLayout.module.css'

interface Props {
  toolbar: React.ReactNode
  topPanel?: React.ReactNode
  leftPanel: React.ReactNode
  middlePanel: React.ReactNode
  rightPanel: React.ReactNode
  bottomPanel?: React.ReactNode
}

export function WorkbenchLayout({
  toolbar,
  topPanel,
  leftPanel,
  middlePanel,
  rightPanel,
  bottomPanel,
}: Props): React.ReactElement {
  return (
    <div className={styles.root}>
      {toolbar}
      {topPanel && <div className={styles.topPanel}>{topPanel}</div>}
      <div className={styles.content}>
        <aside className={styles.leftPanel}>{leftPanel}</aside>
        <main className={styles.middlePanel}>{middlePanel}</main>
        <aside className={styles.rightPanel}>{rightPanel}</aside>
      </div>
      {bottomPanel && <div className={styles.bottomPanel}>{bottomPanel}</div>}
    </div>
  )
}
