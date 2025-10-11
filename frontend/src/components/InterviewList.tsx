import { Link } from 'react-router-dom';
import { Card, CardContent } from './ui/card';
import type { Interview } from '../types/study';

interface InterviewListProps {
  interviews: Interview[];
  orgId: string;
  studyId: string;
}

export function InterviewList({ interviews, orgId, studyId }: InterviewListProps) {
  if (interviews.length === 0) {
    return (
      <div className="text-center py-12" data-testid="empty-interviews">
        <p className="text-muted-foreground text-lg">No interviews completed yet</p>
        <p className="text-muted-foreground text-sm mt-2">
          Completed interviews will appear here
        </p>
      </div>
    );
  }

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return 'Invalid date';
    }
  };

  return (
    <div className="space-y-3" data-testid="interview-list">
      {interviews.map((interview) => (
        <Link
          key={interview.id}
          to={`/orgs/${orgId}/studies/${studyId}/interviews/${interview.id}`}
          data-testid={`interview-${interview.id}`}
        >
          <Card className="hover:bg-muted/50 transition-colors cursor-pointer">
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div className="space-y-1 flex-1">
                  <div className="flex items-center gap-3">
                    <h3 className="font-medium">
                      Interview #{interview.id}
                    </h3>
                    {interview.external_participant_id && (
                      <span
                        className="text-sm px-2 py-0.5 bg-muted rounded"
                        data-testid={`participant-id-${interview.id}`}
                      >
                        {interview.external_participant_id}
                      </span>
                    )}
                    {interview.platform_source && (
                      <span
                        className="text-xs px-2 py-0.5 bg-primary/10 text-primary rounded"
                        data-testid={`platform-${interview.id}`}
                      >
                        {interview.platform_source}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Completed: {formatDate(interview.completed_at)}
                  </p>
                  <div className="flex gap-4 text-sm mt-2">
                    <span
                      className={interview.has_transcript ? 'text-green-600' : 'text-muted-foreground'}
                      data-testid={`transcript-status-${interview.id}`}
                    >
                      {interview.has_transcript ? '✓ Transcript' : '✗ No Transcript'}
                    </span>
                    <span
                      className={interview.has_recording ? 'text-green-600' : 'text-muted-foreground'}
                      data-testid={`recording-status-${interview.id}`}
                    >
                      {interview.has_recording ? '✓ Recording' : '✗ No Recording'}
                    </span>
                  </div>
                </div>
                <div className="text-sm text-muted-foreground">
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                </div>
              </div>
            </CardContent>
          </Card>
        </Link>
      ))}
    </div>
  );
}
