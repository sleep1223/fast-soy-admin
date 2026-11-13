declare namespace Api {
  namespace Ocr {
    type Crop = {
      x: number;
      y: number;
      width: number;
      height: number;
    };

    type Options = {
      crop?: Crop | null;
      useCls?: boolean;
    };

    type Item = {
      text: string;
      confidence: number;
      box: [number, number][];
    };

    type Result = {
      text: string;
      items: Item[];
      elapsedMs: number;
      truncated: boolean;
      width: number;
      height: number;
    };
  }
}
