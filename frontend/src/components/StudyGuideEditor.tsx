import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { Label } from './ui/label';
import type { InterviewGuide } from '../types/study';
import { updateGuide } from '../lib/api';

interface StudyGuideEditorProps {
  studyId: string;
  guide: InterviewGuide;
  onSave: (guide: InterviewGuide) => void;
  onCancel: () => void;
}

export function StudyGuideEditor({ studyId, guide, onSave, onCancel }: StudyGuideEditorProps) {
  const [contentMd, setContentMd] = useState(guide.content_md);
  const [isDirty, setIsDirty] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Track if content has changed
  useEffect(() => {
    setIsDirty(contentMd !== guide.content_md);
  }, [contentMd, guide.content_md]);

  // Warn before leaving with unsaved changes
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (isDirty) {
        e.preventDefault();
        e.returnValue = '';
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [isDirty]);

  const handleSave = async () => {
    setIsSaving(true);
    setError(null);

    const token = localStorage.getItem('firebase_token');
    if (!token) {
      setError('Authentication required');
      setIsSaving(false);
      return;
    }

    try {
      const updatedGuide = await updateGuide(studyId, contentMd, token);
      setIsDirty(false);
      onSave(updatedGuide);
    } catch (err: any) {
      setError(err.message || 'Failed to save guide');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div data-testid="guide-editor" data-dirty={isDirty} className="space-y-4">
      <div className="flex items-center justify-between">
        <Label htmlFor="guide-content">Interview Guide (Markdown)</Label>
        <div className="flex gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            data-testid="preview-toggle"
            onClick={() => setShowPreview(!showPreview)}
          >
            {showPreview ? 'Edit Only' : 'Show Preview'}
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-md text-red-800 text-sm">
          {error}
        </div>
      )}

      <div className={showPreview ? 'grid grid-cols-2 gap-4' : ''}>
        <div className="space-y-2">
          <Textarea
            id="guide-content"
            data-testid="guide-editor-textarea"
            value={contentMd}
            onChange={(e) => setContentMd(e.target.value)}
            placeholder="Enter your interview guide in Markdown format..."
            className="min-h-[400px] font-mono text-sm"
          />
        </div>

        {showPreview && (
          <div className="space-y-2">
            <Label>Preview</Label>
            <div data-testid="guide-preview" className="prose prose-sm max-w-none p-4 border rounded-md bg-gray-50 min-h-[400px] overflow-auto">
              <ReactMarkdown>{contentMd}</ReactMarkdown>
            </div>
          </div>
        )}
      </div>

      <div className="flex justify-end gap-2">
        <Button
          type="button"
          variant="outline"
          onClick={onCancel}
          disabled={isSaving}
        >
          Cancel
        </Button>
        <Button
          type="button"
          onClick={handleSave}
          disabled={isSaving || !isDirty}
        >
          {isSaving ? 'Saving...' : 'Save'}
        </Button>
      </div>
    </div>
  );
}
