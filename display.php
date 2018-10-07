<!DOCTYPE html>
<html>
	<body>
		<table>
			<thead>
				<tr>
					<th>Platz</th>
					<th>Zeit</th>
					<th>Team</th>
					<th>Name</th>
				</tr>
			<thead>
			<tbody>
				<?php
					$scores = file_get_contents("./output.csv");
					$scores = explode("\n", $scores);
					$scores = array_map(function($x)
					{
						$result = explode(",", $x);
						$result[3] = (float)$result[3];
						return $result;
					}, $scores);
					usort($scores, function($a, $b)
					{
						if($a[3] == $b[3])
							return 0;
						else if($a[3] < $b[3])
							return -1;
						else
							return 1;
					});

					foreach($scores as $i => $line)
					{
						?>
				<tr>
					<td><?= $i + 1 ?></td>
					<td><?= sprintf("%.2f", $line[3]) ?></td>
					<td><?= rand(100, 200) ?></td>
					<td><?= $line[0] ?></td>
				</tr>
						<?php
					}
				?>
			</tbody>
	</body>
</html>
