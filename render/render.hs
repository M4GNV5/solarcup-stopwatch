import Data.Ord
import Data.List
import Data.List.Split

scoreRanges = [
        ("schueler", 0, 10),
        ("offen", 11, 30),
        ("firmen", 31, 40)
    ]

fst3 (x,_,_) = x
snd3 (_,x,_) = x
trd3 (_,_,x) = x

parseScore :: [String] -> (Int, String, Double)
parseScore csv          = (read $ csv !! 0, csv !! 1, read $ csv !! 2)

bestScorePerTeam startId stopId scores
                        = sorted
    where
        teamIds         = nub $ filter (\x -> x >= startId && x <= stopId) $ map fst3 scores
        bestScoreOf id  = minimumBy (comparing trd3) $ filter ((==id) . fst3) scores
        bestScores      = map bestScoreOf teamIds
        sorted          = sortBy (comparing trd3) bestScores

renderScores scores     = result
    where
        renderRow place (id, name, time)
                        = concat [
                "<tr>",
                    "<td>", show place, "</td>",
                    "<td>", show time, "</td>",
                    "<td>", show id, "</td>",
                    "<td>", name, "</td>",
                "</tr>",
                "\n"
            ]
        result          = concat $ map (uncurry renderRow) $ zip [1..] scores

handleRange scores (name, startId, stopId) = do
    let bestScores      = bestScorePerTeam startId stopId scores
        html            = renderScores bestScores
    writeFile ("./" ++ name ++ ".part") html

main = do
    output              <- readFile "./../output.csv"
    let scores          = map (parseScore . splitOn ",") $ lines output

    mapM_ (handleRange scores) scoreRanges
