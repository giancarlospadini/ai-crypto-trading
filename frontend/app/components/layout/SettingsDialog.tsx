import { useState, useEffect } from 'react'
import toast from 'react-hot-toast'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Trash2, Plus, Pencil } from 'lucide-react'
import {
  getAccounts as getAccounts,
  createAccount as createAccount,
  updateAccount as updateAccount,
  deleteAccount as deleteAccount,
  testLLMConnection,
  type TradingAccount,
  type TradingAccountCreate,
  type TradingAccountUpdate
} from '@/lib/api'

interface SettingsDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onAccountUpdated?: () => void  // Add callback for when account is updated
}

interface AIAccount extends TradingAccount {
  model?: string
  base_url?: string
  api_key?: string
  custom_instructions?: string
}

interface AIAccountCreate extends TradingAccountCreate {
  model?: string
  base_url?: string
  api_key?: string
  custom_instructions?: string
}

export default function SettingsDialog({ open, onOpenChange, onAccountUpdated }: SettingsDialogProps) {
  const [accounts, setAccounts] = useState<AIAccount[]>([])
  const [loading, setLoading] = useState(false)
  const [showAddForm, setShowAddForm] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [testResult, setTestResult] = useState<string | null>(null)
  const [testing, setTesting] = useState(false)
  const [newAccount, setNewAccount] = useState<AIAccountCreate>({
    name: '',
    model: '',
    base_url: '',
    api_key: 'default-key-please-update-in-settings',
    initial_capital: 10000,
    custom_instructions: '',
  })
  const [editAccount, setEditAccount] = useState<AIAccountCreate>({
    name: '',
    model: '',
    base_url: '',
    api_key: 'default-key-please-update-in-settings',
    custom_instructions: '',
  })

  const loadAccounts = async () => {
    try {
      setLoading(true)
      const data = await getAccounts()
      setAccounts(data)
    } catch (error) {
      console.error('Failed to load accounts:', error)
      toast.error('Failed to load accounts')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (open) {
      loadAccounts()
      setError(null)
      setTestResult(null)
      setShowAddForm(false)
      setEditingId(null)
    }
  }, [open])

  const handleCreateAccount = async () => {
    try {
      setLoading(true)
      setTesting(true)
      setError(null)
      setTestResult(null)

      if (!newAccount.name || !newAccount.name.trim()) {
        setError('Account name is required')
        setLoading(false)
        setTesting(false)
        return
      }

      // If AI fields are provided, test LLM connection first
      if (newAccount.model || newAccount.base_url || newAccount.api_key) {
        setTestResult('Testing LLM connection...')
        try {
          const testResponse = await testLLMConnection({
            model: newAccount.model,
            base_url: newAccount.base_url,
            api_key: newAccount.api_key,
          })
          if (!testResponse.success) {
            const message = testResponse.message || 'LLM connection test failed'
            setError(`LLM Test Failed: ${message}`)
            setTestResult(`❌ Test failed: ${message}`)
            setLoading(false)
            setTesting(false)
            return
          }
          setTestResult('✅ LLM connection test passed! Creating account...')
        } catch (testError) {
          const message = testError instanceof Error ? testError.message : 'LLM connection test failed'
          setError(`LLM Test Failed: ${message}`)
          setTestResult(`❌ Test failed: ${message}`)
          setLoading(false)
          setTesting(false)
          return
        }
      }

      console.log('Creating account with data:', newAccount)
      await createAccount(newAccount)
      setNewAccount({ name: '', model: '', base_url: '', api_key: 'default-key-please-update-in-settings', initial_capital: 10000 })
      setShowAddForm(false)
      await loadAccounts()

      toast.success('Account created successfully!')

      // Notify parent component that account was created
      onAccountUpdated?.()
    } catch (error) {
      console.error('Failed to create account:', error)
      const errorMessage = error instanceof Error ? error.message : 'Failed to create account'
      setError(errorMessage)
      toast.error(`Failed to create account: ${errorMessage}`)
    } finally {
      setLoading(false)
      setTesting(false)
      setTestResult(null)
    }
  }

  const handleUpdateAccount = async () => {
    if (!editingId) return
    try {
      setLoading(true)
      setTesting(true)
      setError(null)
      setTestResult(null)
      
      if (!editAccount.name || !editAccount.name.trim()) {
        setError('Account name is required')
        setLoading(false)
        setTesting(false)
        return
      }
      
      // Test LLM connection first if AI model data is provided
      if (editAccount.model || editAccount.base_url || editAccount.api_key) {
        setTestResult('Testing LLM connection...')
        
        try {
          const testResponse = await testLLMConnection({
            model: editAccount.model,
            base_url: editAccount.base_url,
            api_key: editAccount.api_key
          })
          
          if (!testResponse.success) {
            setError(`LLM Test Failed: ${testResponse.message}`)
            setTestResult(`❌ Test failed: ${testResponse.message}`)
            setLoading(false)
            setTesting(false)
            return
          }
          
          setTestResult('✅ LLM connection test passed!')
        } catch (testError) {
          const errorMessage = testError instanceof Error ? testError.message : 'LLM connection test failed'
          setError(`LLM Test Failed: ${errorMessage}`)
          setTestResult(`❌ Test failed: ${errorMessage}`)
          setLoading(false)
          setTesting(false)
          return
        }
      }
      
      setTesting(false)
      setTestResult('✅ Test passed! Saving account...')
      
      console.log('Updating account with data:', editAccount)
      await updateAccount(editingId, editAccount)
      setEditingId(null)
      setEditAccount({ name: '', model: '', base_url: '', api_key: '' })
      setTestResult(null)
      await loadAccounts()
      
      toast.success('Account updated successfully!')
      
      // Notify parent component that account was updated
      onAccountUpdated?.()
    } catch (error) {
      console.error('Failed to update account:', error)
      const errorMessage = error instanceof Error ? error.message : 'Failed to update account'
      setError(errorMessage)
      setTestResult(null)
      toast.error(`Failed to update account: ${errorMessage}`)
    } finally {
      setLoading(false)
      setTesting(false)
    }
  }

  const startEdit = (account: AIAccount) => {
    setEditingId(account.id)
    setEditAccount({
      name: account.name,
      model: account.model || '',
      base_url: account.base_url || '',
      api_key: account.api_key || '',
      initial_capital: account.initial_capital || 10000,
      custom_instructions: account.custom_instructions || '',
    })
  }

  const cancelEdit = () => {
    setEditingId(null)
    setEditAccount({ name: '', model: '', base_url: '', api_key: 'default-key-please-update-in-settings' })
    setTestResult(null)
    setError(null)
  }

  const handleDeleteAccount = async (accountId: number, accountName: string) => {
    if (!confirm(`Are you sure you want to delete account "${accountName}"? This will delete all associated data (positions, orders, trades).`)) {
      return
    }

    try {
      setLoading(true)
      await deleteAccount(accountId)
      await loadAccounts()
      toast.success('Account deleted successfully!')

      // Notify parent component that account was deleted
      onAccountUpdated?.()
    } catch (error) {
      console.error('Failed to delete account:', error)
      const errorMessage = error instanceof Error ? error.message : 'Failed to delete account'
      toast.error(`Failed to delete account: ${errorMessage}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Account Management</DialogTitle>
          <DialogDescription>
            Manage your trading accounts and AI configurations
          </DialogDescription>
        </DialogHeader>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded">
            {error}
          </div>
        )}

        <div className="space-y-6">
          {/* Existing Accounts */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium">Trading Accounts</h3>
              <Button
                onClick={() => setShowAddForm(!showAddForm)}
                size="sm"
                className="flex items-center gap-2"
              >
                <Plus className="h-4 w-4" />
                Add Account
              </Button>
            </div>

            {loading && accounts.length === 0 ? (
              <div>Loading accounts...</div>
            ) : (
              <div className="space-y-3">
                {accounts.map((account) => (
                  <div key={account.id} className="border rounded-lg p-4">
                    {editingId === account.id ? (
                      <div className="space-y-3">
                        <div className="grid grid-cols-2 gap-3">
                          <Input
                            placeholder="Account name"
                            value={editAccount.name || ''}
                            onChange={(e) => setEditAccount({ ...editAccount, name: e.target.value })}
                          />
                          <Input
                            placeholder="Model"
                            value={editAccount.model || ''}
                            onChange={(e) => setEditAccount({ ...editAccount, model: e.target.value })}
                          />
                        </div>
                        <Input
                          placeholder="Base URL"
                          value={editAccount.base_url || ''}
                          onChange={(e) => setEditAccount({ ...editAccount, base_url: e.target.value })}
                        />
                        <Input
                          placeholder="API Key"
                          type="password"
                          value={editAccount.api_key || ''}
                          onChange={(e) => setEditAccount({ ...editAccount, api_key: e.target.value })}
                        />
                        <div className="bg-yellow-50 border border-yellow-200 rounded p-2">
                          <Input
                            placeholder="Initial Capital (USD)"
                            type="number"
                            value={editAccount.initial_capital || 10000}
                            onChange={(e) => setEditAccount({ ...editAccount, initial_capital: parseFloat(e.target.value) || 10000 })}
                          />
                          <p className="text-xs text-yellow-700 mt-1">⚠️ Warning: Changing capital will reset account balance and clear positions</p>
                        </div>
                        <div className="space-y-2">
                          <label className="text-sm font-medium">Custom AI Instructions (Optional)</label>
                          <textarea
                            placeholder="e.g., 'Focus on meme coins', 'Keep 50% in cash', 'Avoid BTC today'..."
                            className="w-full min-h-[100px] p-2 border rounded-md text-sm resize-vertical"
                            value={editAccount.custom_instructions || ''}
                            onChange={(e) => setEditAccount({ ...editAccount, custom_instructions: e.target.value })}
                          />
                          <p className="text-xs text-muted-foreground">💡 Add specific instructions for the AI to follow when making trading decisions</p>
                        </div>
                        {testResult && (
                          <div className={`text-xs p-2 rounded ${
                            testResult.includes('❌') 
                              ? 'bg-red-50 text-red-700 border border-red-200' 
                              : 'bg-green-50 text-green-700 border border-green-200'
                          }`}>
                            {testResult}
                          </div>
                        )}
                        <div className="flex gap-2">
                          <Button onClick={handleUpdateAccount} disabled={loading || testing} size="sm">
                            {testing ? 'Testing...' : 'Test and Save'}
                          </Button>
                          <Button onClick={cancelEdit} variant="outline" size="sm" disabled={loading || testing}>
                            Cancel
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <div className="flex items-center justify-between">
                        <div className="space-y-1 flex-1">
                          <div className="font-medium">{account.name}</div>
                          <div className="text-xs text-muted-foreground">
                            {account.model ? `Model: ${account.model}` : 'No model configured'}
                          </div>
                          {account.base_url && (
                            <div className="text-xs text-muted-foreground truncate">
                              Base URL: {account.base_url}
                            </div>
                          )}
                          {account.api_key && (
                            <div className="text-xs text-muted-foreground">
                              API Key: {'*'.repeat(Math.max(0, (account.api_key?.length || 0) - 4))}{account.api_key?.slice(-4) || '****'}
                            </div>
                          )}
                          <div className="text-xs text-muted-foreground">
                            Cash: ${account.current_cash?.toLocaleString() || '0'}
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            onClick={() => startEdit(account)}
                            variant="outline"
                            size="sm"
                            disabled={loading}
                          >
                            <Pencil className="h-4 w-4" />
                          </Button>
                          <Button
                            onClick={() => handleDeleteAccount(account.id, account.name)}
                            variant="outline"
                            size="sm"
                            disabled={loading}
                            className="text-red-600 hover:text-red-700 hover:bg-red-50"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Add New Account Form */}
          {showAddForm && (
            <div className="space-y-4 border-t pt-4">
              <h3 className="text-lg font-medium">Add New Account</h3>
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <Input
                    placeholder="Account name"
                    value={newAccount.name || ''}
                    onChange={(e) => setNewAccount({ ...newAccount, name: e.target.value })}
                  />
                  <Input
                    placeholder="Model (e.g., gpt-4)"
                    value={newAccount.model || ''}
                    onChange={(e) => setNewAccount({ ...newAccount, model: e.target.value })}
                  />
                </div>
                <Input
                  placeholder="Base URL (e.g., https://api.openai.com/v1)"
                  value={newAccount.base_url || ''}
                  onChange={(e) => setNewAccount({ ...newAccount, base_url: e.target.value })}
                />
                <Input
                  placeholder="API Key"
                  type="password"
                  value={newAccount.api_key || ''}
                  onChange={(e) => setNewAccount({ ...newAccount, api_key: e.target.value })}
                />
                <Input
                  placeholder="Initial Capital (USD)"
                  type="number"
                  value={newAccount.initial_capital || 10000}
                  onChange={(e) => setNewAccount({ ...newAccount, initial_capital: parseFloat(e.target.value) || 10000 })}
                />
                <div className="space-y-2">
                  <label className="text-sm font-medium">Custom AI Instructions (Optional)</label>
                  <textarea
                    placeholder="e.g., 'Focus on meme coins', 'Keep 50% in cash', 'Avoid BTC today'..."
                    className="w-full min-h-[100px] p-2 border rounded-md text-sm resize-vertical"
                    value={newAccount.custom_instructions || ''}
                    onChange={(e) => setNewAccount({ ...newAccount, custom_instructions: e.target.value })}
                  />
                  <p className="text-xs text-muted-foreground">💡 Add specific instructions for the AI to follow when making trading decisions</p>
                </div>
                <div className="flex gap-2">
                  <Button onClick={handleCreateAccount} disabled={loading}>
                    Test and Create
                  </Button>
                  <Button 
                    onClick={() => setShowAddForm(false)} 
                    variant="outline"
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}