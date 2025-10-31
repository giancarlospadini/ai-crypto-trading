import React, { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { MessageCircle, Send, ChevronDown, ChevronUp } from 'lucide-react'
import { getDecisionQA, askDecisionQuestion, AIDecisionQA } from '@/lib/api'
import { toast } from 'react-hot-toast'

interface DecisionQAProps {
  decisionId: number
}

export default function DecisionQA({ decisionId }: DecisionQAProps) {
  const [expanded, setExpanded] = useState(false)
  const [qaEntries, setQaEntries] = useState<AIDecisionQA[]>([])
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (expanded) {
      loadQA()
    }
  }, [expanded, decisionId])

  const loadQA = async () => {
    try {
      const data = await getDecisionQA(decisionId)
      setQaEntries(data.qa_entries)
    } catch (error) {
      console.error('Error loading Q&A:', error)
    }
  }

  const handleAskQuestion = async () => {
    if (!question.trim()) {
      toast.error('Scrivi una domanda')
      return
    }

    setLoading(true)
    try {
      const newQA = await askDecisionQuestion(decisionId, question)
      setQaEntries([newQA, ...qaEntries])
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
    <div className="border-t mt-2 pt-2">
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setExpanded(!expanded)}
        className="text-xs flex items-center gap-1"
      >
        <MessageCircle className="h-3 w-3" />
        Interroga AI ({qaEntries.length})
        {expanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
      </Button>

      {expanded && (
        <div className="mt-3 space-y-3 bg-muted/30 p-3 rounded-md">
          {/* Question input */}
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="es: Perché hai scelto XRP invece di BTC?"
              className="flex-1 px-3 py-2 text-sm border rounded-md"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !loading) {
                  handleAskQuestion()
                }
              }}
              disabled={loading}
            />
            <Button
              size="sm"
              onClick={handleAskQuestion}
              disabled={loading || !question.trim()}
            >
              {loading ? (
                <span className="animate-spin">⏳</span>
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>

          {/* Q&A entries */}
          <div className="space-y-4 max-h-96 overflow-y-auto">
            {qaEntries.length === 0 ? (
              <p className="text-xs text-muted-foreground text-center py-4">
                Nessuna domanda ancora. Chiedi qualcosa all'AI su questa decisione!
              </p>
            ) : (
              qaEntries.map((qa) => (
                <div key={qa.id} className="bg-background p-3 rounded-md space-y-2 border">
                  <div className="flex items-start gap-2">
                    <span className="text-xs font-semibold text-blue-600">Q:</span>
                    <p className="text-xs flex-1">{qa.question}</p>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="text-xs font-semibold text-green-600">A:</span>
                    <p className="text-xs flex-1 whitespace-pre-wrap">{qa.answer}</p>
                  </div>
                  <p className="text-[10px] text-muted-foreground text-right">
                    {new Date(qa.created_at).toLocaleString('it-IT')}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}
