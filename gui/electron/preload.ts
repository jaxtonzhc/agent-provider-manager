import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('apm', {
  exec: (args: string[]) => ipcRenderer.invoke('apm:exec', args),
})
