import React, { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Send } from 'lucide-react'
import { toast } from 'react-hot-toast'

interface ChatMessage {
  id: number
  question: string
  answer: string
  created_at: string
}

interface AccountChatProps {
  accountId: number
}

export default function AccountChat({ accountId }: AccountChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadChatHistory()
  }, [accountId])

  const loadChatHistory = async () => {
    try {
      const response = await fetch(`http://127.0.0.1:5611/api/account/${accountId}/chat-history`)
      const data = await response.json()
      setMessages(data.chat_history)
    } catch (error) {
      console.error('Error loading chat history:', error)
    }
  }

  const handleAsk = async () => {
    if (!question.trim()) {
      toast.error('Scrivi una domanda')
      return
    }

    setLoading(true)
    try {
      const response = await fetch(`http://127.0.0.1:5611/api/account/${accountId}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question })
      })

      if (!response.ok) {
        throw new Error('Failed to ask question')
      }

      const newMessage = await response.json()
      setMessages([newMessage, ...messages])
      setQuestion('')
      toast.success('Risposta ricevuta!')
    } catch (error: any) {
      toast.error(error.message || 'Errore nel chiedere all\'AI')
      console.error('Error asking question:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-muted/30 p-4 rounded-md space-y-4">
      <h3 className="text-sm font-semibold">💬 Dialoga con l'AI</h3>

      {/* Question input */}
      <div className="flex gap-2">
        <input
          type="text"
          placeholder="es: A quanto penso possa salire XRP prima dell'emissione del ETF?"
          className="flex-1 px-3 py-2 text-sm border rounded-md"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !loading) {
              handleAsk()
            }
          }}
          disabled={loading}
        />
        <Button
          size="sm"
          onClick={handleAsk}
          disabled={loading || !question.trim()}
        >
          {loading ? (
            <span className="animate-spin">⏳</span>
          ) : (
            <Send className="h-4 w-4" />
          )}
        </Button>
      </div>

      {/* Chat history */}
      <div className="space-y-4 max-h-[500px] overflow-y-auto">
        {messages.length === 0 ? (
          <p className="text-xs text-muted-foreground text-center py-8">
            Nessuna conversazione ancora. Fai una domanda all'AI!
          </p>
        ) : (
          messages.map((msg) => (
            <div key={msg.id} className="bg-background p-3 rounded-md space-y-2 border">
              <div className="flex items-start gap-2">
                <span className="text-xs font-semibold text-blue-600">Tu:</span>
                <p className="text-xs flex-1">{msg.question}</p>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-xs font-semibold text-green-600">AI:</span>
                <p className="text-xs flex-1 whitespace-pre-wrap">{msg.answer}</p>
              </div>
              <p className="text-[10px] text-muted-foreground text-right">
                {new Date(msg.created_at).toLocaleString('it-IT')}
              </p>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
