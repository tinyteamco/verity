import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { getReusableStudyLinkUrl } from '../lib/api-interviews';
import type { Study } from '../types/study';

interface StudySettingsProps {
  study: Study;
}

export function StudySettings({ study }: StudySettingsProps) {
  const [copied, setCopied] = useState(false);
  const [expandedPlatform, setExpandedPlatform] = useState<string | null>(null);

  const reusableLinkWithPid = getReusableStudyLinkUrl(study.slug, true);
  const reusableLinkNoPid = getReusableStudyLinkUrl(study.slug, false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(reusableLinkWithPid);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy link:', err);
    }
  };

  const togglePlatform = (platform: string) => {
    setExpandedPlatform(expandedPlatform === platform ? null : platform);
  };

  return (
    <div className="space-y-6" data-testid="study-settings">
      <Card>
        <CardHeader>
          <CardTitle>Reusable Interview Link</CardTitle>
          <CardDescription>
            Share this link with participants to start interviews on-the-fly. Each participant gets a unique interview session.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="reusable-link">Link Template (with participant ID)</Label>
            <div className="flex gap-2">
              <Input
                id="reusable-link"
                data-testid="reusable-link-input"
                value={reusableLinkWithPid}
                readOnly
                className="font-mono text-sm"
              />
              <Button
                data-testid="copy-link-button"
                onClick={handleCopy}
                variant="outline"
              >
                {copied ? 'Copied!' : 'Copy Link'}
              </Button>
            </div>
            <p className="text-sm text-muted-foreground">
              The <code className="px-1 py-0.5 bg-muted rounded">pid</code> parameter is optional but recommended for tracking participants from recruitment platforms.
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="direct-link">Direct Link (no participant ID)</Label>
            <Input
              id="direct-link"
              data-testid="direct-link-input"
              value={reusableLinkNoPid}
              readOnly
              className="font-mono text-sm"
            />
            <p className="text-sm text-muted-foreground">
              Use this version for direct distribution where you don't need to track individual participants.
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Recruitment Platform Integration</CardTitle>
          <CardDescription>
            How to use this link with popular recruitment platforms
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {/* Prolific */}
          <div className="border rounded-lg">
            <button
              className="w-full text-left px-4 py-3 font-medium hover:bg-muted/50 transition-colors flex justify-between items-center"
              onClick={() => togglePlatform('prolific')}
              data-testid="prolific-toggle"
            >
              <span>Prolific</span>
              <span>{expandedPlatform === 'prolific' ? '−' : '+'}</span>
            </button>
            {expandedPlatform === 'prolific' && (
              <div className="px-4 pb-4 space-y-2" data-testid="prolific-instructions">
                <p className="text-sm text-muted-foreground">
                  Prolific uses the variable <code className="px-1 py-0.5 bg-muted rounded">{'{{%PROLIFIC_PID%}}'}</code> for participant IDs.
                </p>
                <div className="bg-muted p-3 rounded text-sm font-mono break-all">
                  {window.location.origin}/study/{study.slug}/start?pid={'{{%PROLIFIC_PID%}}'}
                </div>
                <p className="text-sm text-muted-foreground">
                  Copy this link into your Prolific study's "Completion URL" field. Prolific will automatically substitute the participant ID.
                </p>
              </div>
            )}
          </div>

          {/* Respondent */}
          <div className="border rounded-lg">
            <button
              className="w-full text-left px-4 py-3 font-medium hover:bg-muted/50 transition-colors flex justify-between items-center"
              onClick={() => togglePlatform('respondent')}
              data-testid="respondent-toggle"
            >
              <span>Respondent</span>
              <span>{expandedPlatform === 'respondent' ? '−' : '+'}</span>
            </button>
            {expandedPlatform === 'respondent' && (
              <div className="px-4 pb-4 space-y-2" data-testid="respondent-instructions">
                <p className="text-sm text-muted-foreground">
                  Respondent uses the variable <code className="px-1 py-0.5 bg-muted rounded">{'{{respondent_id}}'}</code> for participant IDs.
                </p>
                <div className="bg-muted p-3 rounded text-sm font-mono break-all">
                  {window.location.origin}/study/{study.slug}/start?pid=respondent_{'{{respondent_id}}'}
                </div>
                <p className="text-sm text-muted-foreground">
                  Add the prefix <code className="px-1 py-0.5 bg-muted rounded">respondent_</code> to help identify the platform source. Include this link when scheduling interviews.
                </p>
              </div>
            )}
          </div>

          {/* UserTesting */}
          <div className="border rounded-lg">
            <button
              className="w-full text-left px-4 py-3 font-medium hover:bg-muted/50 transition-colors flex justify-between items-center"
              onClick={() => togglePlatform('usertesting')}
              data-testid="usertesting-toggle"
            >
              <span>UserTesting</span>
              <span>{expandedPlatform === 'usertesting' ? '−' : '+'}</span>
            </button>
            {expandedPlatform === 'usertesting' && (
              <div className="px-4 pb-4 space-y-2" data-testid="usertesting-instructions">
                <p className="text-sm text-muted-foreground">
                  UserTesting uses the variable <code className="px-1 py-0.5 bg-muted rounded">{'{{tester_id}}'}</code> for participant IDs.
                </p>
                <div className="bg-muted p-3 rounded text-sm font-mono break-all">
                  {window.location.origin}/study/{study.slug}/start?pid=usertesting_{'{{tester_id}}'}
                </div>
                <p className="text-sm text-muted-foreground">
                  Add the prefix <code className="px-1 py-0.5 bg-muted rounded">usertesting_</code> to help identify the platform source. Set this as the study URL in your UserTesting configuration.
                </p>
              </div>
            )}
          </div>

          <div className="mt-4 p-4 bg-muted/50 rounded-lg">
            <h4 className="font-medium mb-2">How it works</h4>
            <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
              <li>Each participant click creates a new interview automatically</li>
              <li>The <code className="px-1 py-0.5 bg-muted rounded">pid</code> parameter tracks participants across platforms</li>
              <li>Same participant ID won't create duplicate interviews</li>
              <li>Platform prefixes (e.g., "prolific_") help you identify the source</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
