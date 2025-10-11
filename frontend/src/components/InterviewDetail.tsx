import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { fetchInterviewTranscript, getInterviewArtifactUrl } from '../lib/api-interviews';
import type { Interview } from '../types/study';

interface InterviewDetailProps {
  interview: Interview;
  orgId: string;
  studyId: string;
}

export function InterviewDetail({ interview, orgId, studyId }: InterviewDetailProps) {
  const navigate = useNavigate();
  const [transcript, setTranscript] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (interview.has_transcript) {
      loadTranscript();
    }
  }, [interview.id]);

  const loadTranscript = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('firebase_token');
      if (!token) {
        throw new Error('No authentication token found');
      }
      const text = await fetchInterviewTranscript(orgId, interview.id, token);
      setTranscript(text);
    } catch (err: any) {
      console.error('Failed to load transcript:', err);
      setError(err.message || 'Failed to load transcript');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadAudio = () => {
    const token = localStorage.getItem('firebase_token');
    if (!token) {
      alert('No authentication token found');
      return;
    }
    const audioUrl = getInterviewArtifactUrl(orgId, interview.id, 'recording.wav', token);
    window.open(audioUrl, '_blank');
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    } catch {
      return 'Invalid date';
    }
  };

  return (
    <div className="space-y-6" data-testid="interview-detail">
      <div className="flex items-center justify-between">
        <div>
          <Button
            variant="outline"
            onClick={() => navigate(`/orgs/${orgId}/studies/${studyId}/interviews`)}
            data-testid="back-to-list-button"
          >
            ← Back to Interviews
          </Button>
        </div>
        <div className="flex gap-2">
          {interview.has_recording && (
            <Button
              onClick={handleDownloadAudio}
              data-testid="download-audio-button"
            >
              Download Audio
            </Button>
          )}
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Interview #{interview.id}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">Status</p>
              <p className="font-medium capitalize">{interview.status}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Completed</p>
              <p className="font-medium">{formatDate(interview.completed_at)}</p>
            </div>
            {interview.external_participant_id && (
              <div>
                <p className="text-muted-foreground">Participant ID</p>
                <p className="font-medium" data-testid="participant-id">
                  {interview.external_participant_id}
                </p>
              </div>
            )}
            {interview.platform_source && (
              <div>
                <p className="text-muted-foreground">Platform Source</p>
                <p className="font-medium capitalize" data-testid="platform-source">
                  {interview.platform_source}
                </p>
              </div>
            )}
          </div>

          <div className="flex gap-4 pt-4 border-t">
            <div className="flex items-center gap-2">
              <span
                className={`w-2 h-2 rounded-full ${
                  interview.has_transcript ? 'bg-green-500' : 'bg-gray-300'
                }`}
              />
              <span className="text-sm">
                {interview.has_transcript ? 'Transcript Available' : 'No Transcript'}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span
                className={`w-2 h-2 rounded-full ${
                  interview.has_recording ? 'bg-green-500' : 'bg-gray-300'
                }`}
              />
              <span className="text-sm">
                {interview.has_recording ? 'Recording Available' : 'No Recording'}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {interview.has_transcript && (
        <Card>
          <CardHeader>
            <CardTitle>Transcript</CardTitle>
          </CardHeader>
          <CardContent>
            {loading && (
              <p className="text-muted-foreground" data-testid="transcript-loading">
                Loading transcript...
              </p>
            )}
            {error && (
              <div className="text-destructive" data-testid="transcript-error">
                <p>Failed to load transcript: {error}</p>
                <Button variant="outline" onClick={loadTranscript} className="mt-2">
                  Retry
                </Button>
              </div>
            )}
            {transcript && !loading && !error && (
              <div
                className="whitespace-pre-wrap font-mono text-sm bg-muted p-4 rounded max-h-96 overflow-y-auto"
                data-testid="transcript-content"
              >
                {transcript}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {!interview.has_transcript && (
        <Card>
          <CardHeader>
            <CardTitle>Transcript</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground" data-testid="transcript-unavailable">
              Transcript not available for this interview
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
