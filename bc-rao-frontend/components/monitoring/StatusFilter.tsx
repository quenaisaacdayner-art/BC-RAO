import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";

interface StatusFilterProps {
  value: string;
  onChange: (status: string) => void;
  counts: {
    all: number;
    active: number;
    removed: number;
    shadowbanned: number;
  };
}

export default function StatusFilter({ value, onChange, counts }: StatusFilterProps) {
  return (
    <Tabs value={value} onValueChange={onChange}>
      <TabsList>
        <TabsTrigger value="">
          All
          <Badge variant="secondary" className="ml-2">
            {counts.all}
          </Badge>
        </TabsTrigger>
        <TabsTrigger value="Ativo">
          Active
          <Badge variant="secondary" className="ml-2">
            {counts.active}
          </Badge>
        </TabsTrigger>
        <TabsTrigger value="Removido">
          Removed
          <Badge variant="secondary" className="ml-2">
            {counts.removed}
          </Badge>
        </TabsTrigger>
        <TabsTrigger value="Shadowbanned">
          Shadowbanned
          <Badge variant="secondary" className="ml-2">
            {counts.shadowbanned}
          </Badge>
        </TabsTrigger>
      </TabsList>
    </Tabs>
  );
}
