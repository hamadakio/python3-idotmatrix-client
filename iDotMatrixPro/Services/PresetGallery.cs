using System.Collections.Generic;

namespace iDotMatrixPro.Services;

public class PixelArtPreset
{
    public string Name { get; set; } = "";
    public string Category { get; set; } = "";
    public uint[,] Pixels { get; set; } = new uint[32, 32];
}

public static class PresetGallery
{
    public static List<PixelArtPreset> GetPresets()
    {
        var list = new List<PixelArtPreset>();

        // 1. Coração 8-bit (Heart)
        list.Add(CreateHeartPreset());

        // 2. Cogumelo Super Mario 1-UP (Mushroom)
        list.Add(CreateMushroomPreset());

        // 3. Space Invader
        list.Add(CreateSpaceInvaderPreset());

        // 4. Pac-Man & Fantasma
        list.Add(CreatePacmanPreset());

        // 5. Caveira Cyberpunk
        list.Add(CreateSkullPreset());

        // 6. Fogo / Chama Pixel
        list.Add(CreateFirePreset());

        return list;
    }

    private static PixelArtPreset CreateHeartPreset()
    {
        var p = new PixelArtPreset { Name = "Coração Retrô", Category = "Games & Emojis" };
        uint red = 0xFFFF0055;
        uint darkRed = 0xFF990022;
        uint white = 0xFFFFFFFF;

        string[] art = [
            "  RRRR    RRRR  ",
            " RWWWRR  RRRRRR ",
            "RWWWWWRRRRRRRRRR",
            "RWWWWWRRRRRRRRRR",
            " RRRRRRRRRRRRRR ",
            "  RRRRRRRRRRRR  ",
            "   RRRRRRRRRR   ",
            "    RRRRRRRR    ",
            "     RRRRRR     ",
            "      RRRR      ",
            "       RR       "
        ];

        int startY = 10;
        int startX = 8;
        for (int r = 0; r < art.Length; r++)
        {
            for (int c = 0; c < art[r].Length; c++)
            {
                char ch = art[r][c];
                if (ch == 'R') p.Pixels[startX + c, startY + r] = red;
                else if (ch == 'W') p.Pixels[startX + c, startY + r] = white;
                else if (ch == 'D') p.Pixels[startX + c, startY + r] = darkRed;
            }
        }
        return p;
    }

    private static PixelArtPreset CreateMushroomPreset()
    {
        var p = new PixelArtPreset { Name = "Cogumelo 1-UP", Category = "Nintendo" };
        uint green = 0xFF00E676;
        uint white = 0xFFFFFFFF;
        uint skin = 0xFFFFE0B2;
        uint eye = 0xFF000000;

        string[] art = [
            "     GGGGGG     ",
            "   GGGGGGGGGG   ",
            "  GGWWGGGGWWGG  ",
            " GWWWWGGGGWWWWG ",
            " GWWWWGGGGWWWWG ",
            "GGWWWWGGGGWWWWGG",
            "GGGGGGWWWWGGGGGG",
            "GGGGGGWWWWGGGGGG",
            " GGGGGWWWWGGGGG ",
            "   SSSSSSSSSS   ",
            "  SSBSSBSSBSSS  ",
            "  SSBSSBSSBSSS  ",
            "  SSSSSSSSSSSS  ",
            "   SSSSSSSSSS   "
        ];

        int startY = 8;
        int startX = 8;
        for (int r = 0; r < art.Length; r++)
        {
            for (int c = 0; c < art[r].Length; c++)
            {
                char ch = art[r][c];
                if (ch == 'G') p.Pixels[startX + c, startY + r] = green;
                else if (ch == 'W') p.Pixels[startX + c, startY + r] = white;
                else if (ch == 'S') p.Pixels[startX + c, startY + r] = skin;
                else if (ch == 'B') p.Pixels[startX + c, startY + r] = eye;
            }
        }
        return p;
    }

    private static PixelArtPreset CreateSpaceInvaderPreset()
    {
        var p = new PixelArtPreset { Name = "Space Invader", Category = "Arcade" };
        uint cyan = 0xFF00E5FF;

        string[] art = [
            "  X     X  ",
            "   X   X   ",
            "  XXXXXXX  ",
            " XX XXX XX ",
            "XXXXXXXXXXX",
            "X XXXXXXX X",
            "X X     X X",
            "   XX XX   "
        ];

        int startY = 12;
        int startX = 10;
        for (int r = 0; r < art.Length; r++)
        {
            for (int c = 0; c < art[r].Length; c++)
            {
                if (art[r][c] == 'X') p.Pixels[startX + c, startY + r] = cyan;
            }
        }
        return p;
    }

    private static PixelArtPreset CreatePacmanPreset()
    {
        var p = new PixelArtPreset { Name = "Pac-Man & Red", Category = "Arcade" };
        uint yellow = 0xFFFFEA00;
        uint red = 0xFFFF1744;
        uint white = 0xFFFFFFFF;
        uint blue = 0xFF2979FF;

        // Pac-man left, ghost right
        string[] art = [
            "  YYYY    RRRR  ",
            " YYYYYY  RRRRRR ",
            "YYYYYYY  RWBWRB ",
            "YYYY     RRRRRR ",
            "YYYY     RRRRRR ",
            "YYYYYYY  RRRRRR ",
            " YYYYYY  R R  R ",
            "  YYYY   R R  R "
        ];

        int startY = 12;
        int startX = 8;
        for (int r = 0; r < art.Length; r++)
        {
            for (int c = 0; c < art[r].Length; c++)
            {
                char ch = art[r][c];
                if (ch == 'Y') p.Pixels[startX + c, startY + r] = yellow;
                else if (ch == 'R') p.Pixels[startX + c, startY + r] = red;
                else if (ch == 'W') p.Pixels[startX + c, startY + r] = white;
                else if (ch == 'B') p.Pixels[startX + c, startY + r] = blue;
            }
        }
        return p;
    }

    private static PixelArtPreset CreateSkullPreset()
    {
        var p = new PixelArtPreset { Name = "Caveira Cyberpunk", Category = "Cyberpunk" };
        uint neonPink = 0xFFFF007F;

        string[] art = [
            "    CCCCCC    ",
            "  CCCCCCCCCC  ",
            " CCCCCCCCCCCC ",
            " CCCCCCCCCCCC ",
            " CC  CCCC  CC ",
            " CC  CCCC  CC ",
            "  CCCCCCCCCC  ",
            "   CCCCCCCC   ",
            "   C C  C C   ",
            "   CCCCCCCC   "
        ];

        int startY = 10;
        int startX = 9;
        for (int r = 0; r < art.Length; r++)
        {
            for (int c = 0; c < art[r].Length; c++)
            {
                if (art[r][c] == 'C') p.Pixels[startX + c, startY + r] = neonPink;
            }
        }
        return p;
    }

    private static PixelArtPreset CreateFirePreset()
    {
        var p = new PixelArtPreset { Name = "Chama Retrô", Category = "Elementos" };
        uint orange = 0xFFFF6D00;
        uint yellow = 0xFFFFD600;
        uint red = 0xFFD50000;

        string[] art = [
            "      O       ",
            "     OO       ",
            "     OYO      ",
            "    OOYOO     ",
            "   OOYYYOO    ",
            "  ROOYYYYOR   ",
            "  RROYYYOOR   ",
            "  RRROYOORR   ",
            "   RRRRRRR    "
        ];

        int startY = 11;
        int startX = 9;
        for (int r = 0; r < art.Length; r++)
        {
            for (int c = 0; c < art[r].Length; c++)
            {
                char ch = art[r][c];
                if (ch == 'Y') p.Pixels[startX + c, startY + r] = yellow;
                else if (ch == 'O') p.Pixels[startX + c, startY + r] = orange;
                else if (ch == 'R') p.Pixels[startX + c, startY + r] = red;
            }
        }
        return p;
    }
}
