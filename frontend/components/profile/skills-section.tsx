"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { MultiSkillEditor } from "./multi-skill-editor";

export function SkillsSection() {
  return (
    <Card className="w-full border-border shadow-xs">
      <CardHeader>
        <CardTitle>Skills & Proficiencies</CardTitle>
        <CardDescription>
          Add and manage your technical abilities, tools, and proficiencies. You can stage multiple skills before saving.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <MultiSkillEditor />
      </CardContent>
    </Card>
  );
}
