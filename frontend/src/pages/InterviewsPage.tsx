import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { InterviewList } from '../components/InterviewList';
import { InterviewDetail } from '../components/InterviewDetail';
import { listStudyInterviews } from '../lib/api-interviews';
import type { Interview } from '../types/study';

export function InterviewsPage() {
  const { orgId, studyId, interviewId } = useParams<{
    orgId: string;
    studyId: string;
    interviewId?: string;
  }>();

  const [interviews, setInterviews] = useState<Interview[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchInterviews();
  }, [orgId, studyId]);

  const fetchInterviews = async () => {
    if (!orgId || !studyId) return;

    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('firebase_token');
      if (!token) {
        throw new Error('No authentication token found');
      }

      const data = await listStudyInterviews(orgId, studyId, token);
      setInterviews(data.interviews);
    } catch (err: any) {
      console.error('[InterviewsPage] Error fetching interviews:', err);
      setError(err.message || 'Failed to load interviews');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6" data-testid="interviews-loading">
        <p className="text-muted-foreground">Loading interviews...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6" data-testid="interviews-error">
        <div className="text-destructive">
          <p className="font-medium">Failed to load interviews</p>
          <p className="text-sm mt-1">{error}</p>
          <button
            onClick={fetchInterviews}
            className="mt-4 px-4 py-2 border rounded hover:bg-muted"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // If interviewId is provided, find and display that specific interview
  if (interviewId && orgId && studyId) {
    const interview = interviews.find((i) => i.id === parseInt(interviewId, 10));

    if (!interview) {
      return (
        <div className="p-6" data-testid="interview-not-found">
          <p className="text-destructive font-medium">Interview not found</p>
          <p className="text-sm text-muted-foreground mt-1">
            The interview you're looking for doesn't exist or you don't have access to it.
          </p>
        </div>
      );
    }

    return (
      <div className="p-6">
        <InterviewDetail interview={interview} orgId={orgId} studyId={studyId} />
      </div>
    );
  }

  // Otherwise, show the list view
  return (
    <div className="p-6 space-y-6" data-testid="interviews-page">
      <div>
        <h1 className="text-3xl font-bold">Interviews</h1>
        <p className="text-muted-foreground mt-1">
          View completed interviews and their artifacts
        </p>
      </div>

      <InterviewList interviews={interviews} orgId={orgId!} studyId={studyId!} />
    </div>
  );
}
