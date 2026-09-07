import { app } from 'electron'
import { promises as fs } from 'fs'
import path from 'path'
import type { CompanyConfig } from '../shared/types'

function configPath(): string {
  return path.join(app.getPath('userData'), 'company.json')
}

export async function getConfig(): Promise<CompanyConfig | null> {
  try {
    const data = await fs.readFile(configPath(), 'utf-8')
    const parsed = JSON.parse(data)
    if (
      !parsed ||
      typeof parsed !== 'object' ||
      typeof parsed.name !== 'string' ||
      typeof parsed.cnpj !== 'string' ||
      typeof parsed.city !== 'string'
    ) return null
    return parsed as CompanyConfig
  } catch {
    return null
  }
}

export async function setConfig(config: CompanyConfig): Promise<void> {
  await fs.mkdir(path.dirname(configPath()), { recursive: true })
  await fs.writeFile(configPath(), JSON.stringify(config, null, 2), 'utf-8')
}

function recentPath(): string {
  return path.join(app.getPath('userData'), 'recent.json')
}

export async function getRecent(): Promise<string[]> {
  try {
    const data = await fs.readFile(recentPath(), 'utf-8')
    const parsed = JSON.parse(data)
    return Array.isArray(parsed) ? parsed.filter((x): x is string => typeof x === 'string') : []
  } catch {
    return []
  }
}

export async function addRecent(filePath: string): Promise<void> {
  const current = await getRecent()
  const updated = [filePath, ...current.filter((p) => p !== filePath)].slice(0, 5)
  await fs.writeFile(recentPath(), JSON.stringify(updated), 'utf-8')
}
